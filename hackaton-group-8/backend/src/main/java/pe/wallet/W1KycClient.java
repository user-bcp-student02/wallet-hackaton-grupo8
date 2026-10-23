package pe.wallet;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

@ApplicationScoped
public class W1KycClient {
    private static final Set<String> SCENARIOS = Set.of("APPROVED", "MANUAL_REVIEW", "REJECTED", "UNAVAILABLE");
    private final String baseUrl;
    private final HttpClient http;
    private final ObjectMapper mapper;

    public record Verification(String id, @JsonProperty("wallet_id") String walletId, String scenario, String status) {}
    public record WalletSnapshot(String id, String status, Long balance, Long reserved, Long available, String currency) {}
    public record SupportCase(String id, String resource, String reason, String status) {}

    @Inject
    public W1KycClient(@ConfigProperty(name = "w1.base-url", defaultValue = "UNCONFIGURED") String baseUrl, ObjectMapper mapper) {
        this(baseUrl, HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build(), mapper);
    }

    W1KycClient(String baseUrl, HttpClient http, ObjectMapper mapper) {
        this.baseUrl = baseUrl == null || baseUrl.equals("UNCONFIGURED")
                ? "" : baseUrl.strip().replaceAll("/+$", "");
        this.http = http;
        this.mapper = mapper;
    }

    public Verification createVerification(String document, String scenario) {
        requireDocument(document);
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("documentType", "TEST");
        body.put("document", document);
        if (scenario != null && !scenario.isBlank()) {
            require(SCENARIOS.contains(scenario), "INVALID_SCENARIO", "Escenario KYC W1 inválido.");
            body.put("scenario", scenario);
        }
        Verification result = decode(request("POST", "/kyc/verifications", body, 201), Verification.class);
        validateVerification(result);
        return result;
    }

    public Verification getVerification(String id) {
        Verification result = decode(request("GET", "/kyc/verifications/" + segment(id), null, 200), Verification.class);
        validateVerification(result);
        return result;
    }

    public WalletSnapshot getWallet(String id) {
        WalletSnapshot result = decode(request("GET", "/wallets/" + segment(id), null, 200), WalletSnapshot.class);
        if (blank(result.id()) || blank(result.status()) || result.balance() == null || result.reserved() == null
                || result.available() == null || blank(result.currency())) {
            throw contractError("La consulta de wallet omitió campos publicados por W1.");
        }
        return result;
    }

    public List<SupportCase> getSupportCases() {
        List<SupportCase> cases = decodeList(request("GET", "/support/cases", null, 200));
        if (cases.stream().anyMatch(c -> blank(c.id()) || blank(c.resource()) || blank(c.reason()) || blank(c.status()))) {
            throw contractError("La respuesta de soporte omitió campos publicados por W1.");
        }
        return cases;
    }

    public Verification decide(String verificationId, String decision) {
        require(decision != null && Set.of("ACTIVE", "REJECTED").contains(decision),
                "INVALID_DECISION", "La decisión KYC debe ser ACTIVE o REJECTED.");
        Verification result = decode(request("POST", "/kyc/verifications/" + segment(verificationId) + "/decision",
                Map.of("decision", decision), 200), Verification.class);
        validateVerification(result);
        return result;
    }

    private HttpResponse<String> request(String method, String path, Object body, int expectedStatus) {
        if (baseUrl.isBlank()) {
            throw new ApiError(503, "W1_NOT_CONFIGURED", "La URL del servicio KYC W1 no está configurada.");
        }
        URI uri;
        try {
            uri = URI.create(baseUrl + path);
        } catch (IllegalArgumentException error) {
            throw new ApiError(500, "W1_CONFIGURATION_ERROR", "La URL del servicio KYC W1 no es válida.");
        }
        if (uri.getScheme() == null || !Set.of("http", "https").contains(uri.getScheme()) || blank(uri.getHost())) {
            throw new ApiError(500, "W1_CONFIGURATION_ERROR", "La URL del servicio KYC W1 debe usar HTTP o HTTPS.");
        }
        HttpRequest.Builder request = HttpRequest.newBuilder(uri)
                .timeout(Duration.ofSeconds(10))
                .header("Accept", "application/json");
        if (body == null) {
            request.method(method, HttpRequest.BodyPublishers.noBody());
        } else {
            try {
                request.header("Content-Type", "application/json")
                        .method(method, HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(body)));
            } catch (JsonProcessingException error) {
                throw new IllegalStateException("Could not serialize W1 request", error);
            }
        }
        HttpResponse<String> response;
        try {
            response = http.send(request.build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new ApiError(503, "W1_REQUEST_INTERRUPTED", "La solicitud KYC fue interrumpida; no se confirmó su resultado.");
        } catch (IOException error) {
            throw new ApiError(503, "W1_CONNECTION_FAILED", "No se pudo confirmar la respuesta del servicio KYC; consulta el estado antes de reintentar.");
        }
        if (response.statusCode() != expectedStatus) {
            throw externalError(response);
        }
        return response;
    }

    private ApiError externalError(HttpResponse<String> response) {
        JsonNode body;
        try {
            body = mapper.readTree(response.body());
        } catch (JsonProcessingException error) {
            body = null;
        }
        if (body != null) {
            String code = body.path("code").asText("");
            String message = body.path("message").asText("");
            if (!blank(code) && !blank(message)) {
                return new ApiError(response.statusCode(), code, message);
            }
        }
        if (response.statusCode() == 503) {
            return new ApiError(503, "KYC_UNAVAILABLE", "El servicio de verificación no está disponible.");
        }
        return new ApiError(response.statusCode(), "W1_HTTP_ERROR", "El servicio KYC rechazó la solicitud.");
    }

    private <T> T decode(HttpResponse<String> response, Class<T> type) {
        try {
            return mapper.readValue(response.body(), type);
        } catch (JsonProcessingException error) {
            throw contractError("La respuesta W1 no es JSON válido para el contrato publicado.");
        }
    }

    private List<SupportCase> decodeList(HttpResponse<String> response) {
        try {
            List<SupportCase> result = mapper.readValue(response.body(), new TypeReference<>() {});
            if (result == null) throw contractError("La respuesta de casos de soporte W1 no puede ser nula.");
            return result;
        } catch (JsonProcessingException error) {
            throw contractError("La respuesta de casos de soporte W1 no es una lista válida.");
        }
    }

    private static void validateVerification(Verification verification) {
        if (blank(verification.id()) || blank(verification.walletId()) || verification.id().equals(verification.walletId())
                || verification.scenario() == null || !SCENARIOS.contains(verification.scenario())
                || blank(verification.status())) {
            throw contractError("La respuesta KYC omitió o mezcló identificadores publicados por W1.");
        }
    }

    private static void requireDocument(String document) {
        if (document == null || !document.matches("TEST-[A-Za-z0-9-]{1,80}")) {
            throw new ApiError(400, "TEST_DOCUMENT_REQUIRED", "W1 solo admite documentos ficticios con prefijo TEST-.");
        }
    }

    private static String segment(String value) {
        if (blank(value)) throw new ApiError(400, "W1_ID_REQUIRED", "Se requiere el identificador publicado por W1.");
        return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20");
    }

    private static ApiError contractError(String message) {
        return new ApiError(502, "W1_CONTRACT_ERROR", message);
    }

    private static boolean blank(String value) {
        return value == null || value.isBlank();
    }

    private static void require(boolean condition, String code, String message) {
        if (!condition) throw new ApiError(400, code, message);
    }
}

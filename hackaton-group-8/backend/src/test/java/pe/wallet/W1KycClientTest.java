package pe.wallet;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.http.HttpClient;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

class W1KycClientTest {
    private final ObjectMapper mapper = new ObjectMapper();
    private final AtomicInteger sequence = new AtomicInteger();
    private final Map<String, W1KycClient.Verification> verifications = new LinkedHashMap<>();
    private final Map<String, W1KycClient.WalletSnapshot> wallets = new LinkedHashMap<>();
    private final List<W1KycClient.SupportCase> cases = new ArrayList<>();
    private final List<String> receivedDocuments = new ArrayList<>();
    private final List<Map<?, ?>> receivedBodies = new ArrayList<>();
    private HttpServer server;
    private W1KycClient client;

    @BeforeEach
    void startContractServer() throws IOException {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/", this::handle);
        server.start();
        client = new W1KycClient("http://127.0.0.1:" + server.getAddress().getPort(),
                HttpClient.newHttpClient(), mapper);
    }

    @AfterEach
    void stopContractServer() {
        server.stop(0);
    }

    @Test
    void usesPublishedCreateQueryWalletAndSupportContracts() {
        W1KycClient.Verification created = client.createVerification("TEST-001", "MANUAL_REVIEW");

        assertEquals("kyc-1", created.id());
        assertEquals("wallet-1", created.walletId());
        assertFalse(created.status().isBlank());
        assertEquals(List.of("TEST-001"), receivedDocuments);
        assertEquals(java.util.Set.of("documentType", "document", "scenario"), receivedBodies.getFirst().keySet());
        assertEquals(created, client.getVerification(created.id()));

        W1KycClient.WalletSnapshot wallet = client.getWallet(created.walletId());
        assertEquals("PENDING", wallet.status());
        assertEquals(0L, wallet.balance());
        assertEquals(0L, wallet.reserved());
        assertEquals(0L, wallet.available());
        assertEquals("PEN", wallet.currency());

        List<W1KycClient.SupportCase> supportCases = client.getSupportCases();
        assertEquals(1, supportCases.size());
        assertEquals("case-1", supportCases.getFirst().id());
        assertFalse(supportCases.getFirst().resource().isBlank());
        assertFalse(supportCases.getFirst().reason().isBlank());
        assertEquals("OPEN", supportCases.getFirst().status());
    }

    @Test
    void approvedScenarioIsOptionalAndClientNeverSendsIdentityOrPinFields() {
        W1KycClient.Verification result = client.createVerification("TEST-DEFAULT", null);
        assertEquals("APPROVED", result.scenario());
        assertEquals(java.util.Set.of("documentType", "document"), receivedBodies.getFirst().keySet());
    }

    @Test
    void characterizesAllFourW1ScenariosAndUnavailableCreatesNoWallet() {
        for (String scenario : List.of("APPROVED", "MANUAL_REVIEW", "REJECTED")) {
            W1KycClient.Verification result = client.createVerification("TEST-" + scenario.replace('_', '-'), scenario);
            assertEquals(scenario, result.scenario());
            String expectedWalletStatus = switch (scenario) {
                case "APPROVED" -> "ACTIVE";
                case "MANUAL_REVIEW" -> "PENDING";
                default -> "REJECTED";
            };
            assertEquals(result, client.getVerification(result.id()));
            assertEquals(expectedWalletStatus, client.getWallet(result.walletId()).status());
            assertEquals(0L, client.getWallet(result.walletId()).balance());
        }

        int walletCount = wallets.size();
        ApiError unavailable = assertThrows(ApiError.class,
                () -> client.createVerification("TEST-UNAVAILABLE", "UNAVAILABLE"));
        assertEquals(503, unavailable.getResponse().getStatus());
        assertEquals("KYC_UNAVAILABLE", ((Map<?, ?>) unavailable.getResponse().getEntity()).get("code"));
        assertEquals(walletCount, wallets.size());
    }

    @Test
    void finalDecisionsAreIdempotentAndChangingOneConflicts() {
        W1KycClient.Verification pending = client.createVerification("TEST-DECISION", "MANUAL_REVIEW");

        W1KycClient.Verification finalDecision = client.decide(pending.id(), "ACTIVE");
        assertEquals(finalDecision, client.decide(pending.id(), "ACTIVE"));

        ApiError conflict = assertThrows(ApiError.class, () -> client.decide(pending.id(), "REJECTED"));
        assertEquals(409, conflict.getResponse().getStatus());
        assertTrue(conflict.getMessage().contains("DECISION_CONFLICT"));
        assertEquals(finalDecision, client.getVerification(pending.id()));
    }

    @Test
    void rejectsNonTestDocumentsAndReportsMissingBaseUrlExplicitly() {
        assertThrows(ApiError.class, () -> client.createVerification("123456", null));
        W1KycClient unconfigured = new W1KycClient("", HttpClient.newHttpClient(), mapper);
        ApiError error = assertThrows(ApiError.class, () -> unconfigured.createVerification("TEST-002", null));
        assertEquals(503, error.getResponse().getStatus());
        assertEquals("W1_NOT_CONFIGURED", ((Map<?, ?>) error.getResponse().getEntity()).get("code"));
    }

    private void handle(HttpExchange exchange) throws IOException {
        String path = exchange.getRequestURI().getPath();
        String method = exchange.getRequestMethod();
        if (method.equals("POST") && path.equals("/kyc/verifications")) {
            create(exchange);
        } else if (method.equals("GET") && path.equals("/kyc/verifications/kyc-1")) {
            respond(exchange, 200, mapper.writeValueAsString(verifications.get("kyc-1")));
        } else if (method.equals("GET") && path.startsWith("/kyc/verifications/")) {
            String id = path.substring("/kyc/verifications/".length());
            W1KycClient.Verification verification = verifications.get(id);
            respond(exchange, verification == null ? 404 : 200, verification == null
                    ? "{\"code\":\"NOT_FOUND\",\"message\":\"Not found\"}" : mapper.writeValueAsString(verification));
        } else if (method.equals("GET") && path.startsWith("/wallets/")) {
            String id = path.substring("/wallets/".length());
            W1KycClient.WalletSnapshot wallet = wallets.get(id);
            respond(exchange, wallet == null ? 404 : 200, wallet == null
                    ? "{\"code\":\"NOT_FOUND\",\"message\":\"Not found\"}" : mapper.writeValueAsString(wallet));
        } else if (method.equals("GET") && path.equals("/support/cases")) {
            respond(exchange, 200, mapper.writeValueAsString(cases));
        } else if (method.equals("POST") && path.endsWith("/decision")) {
            decide(exchange, path.substring("/kyc/verifications/".length(), path.length() - "/decision".length()));
        } else {
            respond(exchange, 404, "{\"code\":\"NOT_FOUND\",\"message\":\"Not found\"}");
        }
    }

    private void create(HttpExchange exchange) throws IOException {
        Map<?, ?> request = mapper.readValue(exchange.getRequestBody(), Map.class);
        receivedBodies.add(request);
        assertEquals("TEST", request.get("documentType"));
        String document = request.get("document").toString();
        assertTrue(document.startsWith("TEST-"));
        receivedDocuments.add(document);
        String scenario = request.containsKey("scenario") ? request.get("scenario").toString() : "APPROVED";
        if (scenario.equals("UNAVAILABLE")) {
            respond(exchange, 503, "{\"code\":\"KYC_UNAVAILABLE\",\"message\":\"Unavailable\"}");
            return;
        }
        int number = sequence.incrementAndGet();
        String id = "kyc-" + number;
        String walletId = "wallet-" + number;
        String status = switch (scenario) {
            case "APPROVED" -> "ACTIVE";
            case "MANUAL_REVIEW" -> "PENDING";
            case "REJECTED" -> "REJECTED";
            default -> throw new IllegalArgumentException("Unexpected scenario");
        };
        W1KycClient.Verification verification = new W1KycClient.Verification(id, walletId, scenario, status);
        verifications.put(id, verification);
        wallets.put(walletId, new W1KycClient.WalletSnapshot(walletId, status, 0L, 0L, 0L, "PEN"));
        if (scenario.equals("MANUAL_REVIEW")) {
            cases.add(new W1KycClient.SupportCase("case-" + number, walletId, "KYC_REVIEW", "OPEN"));
        }
        respond(exchange, 201, mapper.writeValueAsString(verification));
    }

    private void decide(HttpExchange exchange, String verificationId) throws IOException {
        Map<?, ?> request = mapper.readValue(exchange.getRequestBody(), Map.class);
        W1KycClient.Verification existing = verifications.get(verificationId);
        if (existing == null) {
            respond(exchange, 404, "{\"code\":\"NOT_FOUND\",\"message\":\"Not found\"}");
            return;
        }
        String decision = request.get("decision").toString();
        if (!existing.status().equals("PENDING")) {
            if (existing.status().equals(decision)) {
                respond(exchange, 200, mapper.writeValueAsString(existing));
            } else {
                respond(exchange, 409, "{\"code\":\"DECISION_CONFLICT\",\"message\":\"DECISION_CONFLICT\"}");
            }
            return;
        }
        W1KycClient.Verification result = new W1KycClient.Verification(existing.id(), existing.walletId(),
                existing.scenario(), decision);
        verifications.put(verificationId, result);
        W1KycClient.WalletSnapshot oldWallet = wallets.get(existing.walletId());
        wallets.put(existing.walletId(), new W1KycClient.WalletSnapshot(oldWallet.id(), decision, 0L, 0L, 0L, "PEN"));
        cases.replaceAll(support -> support.resource().equals(existing.walletId())
                ? new W1KycClient.SupportCase(support.id(), support.resource(), support.reason(), "RESOLVED") : support);
        respond(exchange, 200, mapper.writeValueAsString(result));
    }

    private static void respond(HttpExchange exchange, int status, String body) throws IOException {
        byte[] bytes = body.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length);
        try (var output = exchange.getResponseBody()) {
            output.write(bytes);
        }
    }
}

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import java.net.InetSocketAddress;
import java.io.IOException;
import java.io.OutputStream;

public class VulnerableApp {
    private static final Logger logger = LogManager.getLogger(VulnerableApp.class);

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/", new LogHandler());
        server.setExecutor(null);

        System.out.println("Vulnerable Log4j server started on http://localhost:8080");
        logger.info("Server started - waiting for requests");

        server.start();
    }

    static class LogHandler implements HttpHandler {
        private static final Logger logger = LogManager.getLogger(LogHandler.class);

        public void handle(HttpExchange exchange) throws IOException {
            String userInput = exchange.getRequestHeaders().getFirst("User-Agent");
            if (userInput == null) {
                userInput = exchange.getRequestURI().getQuery();
            }
            if (userInput == null) {
                userInput = "anonymous";
            }

            // VULNERABLE: Log user input directly - this is where Log4Shell happens
            logger.error("Request from: " + userInput);

            String response = "Request logged successfully";
            exchange.sendResponseHeaders(200, response.length());
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        }
    }
}
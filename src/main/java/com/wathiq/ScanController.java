package com.wathiq;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.util.HashMap;
import java.util.Map;

/**
 * <h3>API Gateway</h3>
 * <p>
 *     This class controls the web links for the Wathiq system.
 *     It receives HTTP requests from the front-end and sends the work to the Service layer to be processed.
 * </p>
 * <strong>Base URL:</strong> /api
 */

@RestController
@RequestMapping("/api")
public class ScanController {

    @Autowired
    private OcrService ocrService;

    /**
     * <strong>Endpoints:</strong> POST /api/scan <br>
     * <strong>Usage:</strong> Uploads a document for validation.
     * <p><strong>Request Format:</strong> Multipart FormData</p>
     * <strong>key:</strong> "File" (The image to scan)
     * <p><strong>Response Format (JSON):</strong></p>
     * <pre>
     *     {
     *         "text": "The extracted Arabic test...",
     *         "isValid": true/false (Based on keyword check)
     *     }
     * </pre>
     * @param file The document image uploaded by the user.
     * @return JSON response containing the text and the validation status.
     */
    @PostMapping("/scan")
    public ResponseEntity<Map<String, Object>> scanDocument(@RequestParam("file") MultipartFile file){
        // 1. The OCR logic in the service.
        String extractedText = ocrService.extractText(file);

        // 2. Preparing the Response Data.
        Map<String, Object> response = new HashMap<>();
        response.put("text", extractedText);

        // 3. Simple Validation Logic
        // Checks if the document contains specified keywords.
        boolean valid = extractedText.contains("واثق")
                || extractedText.contains("تجربة");
        response.put("isValid", valid);

        return ResponseEntity.ok(response);
    }
}

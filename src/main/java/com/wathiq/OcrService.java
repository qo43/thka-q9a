package com.wathiq;

import net.sourceforge.tess4j.Tesseract;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import javax.imageio.ImageIO;

import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.image.BufferedImage;

import java.io.File;
import java.io.FileOutputStream;

/**
 * <h3>The OCR Engine</h3>
 * <p>
 *     This class handles the Computer Vision Logic. It acts as a bridge between the backend (Spring Boot)
 *     and the local Tesseract Library.
 * </p>
 * <strong>Features:</strong>
 * <p>
 *     Privacy is implemented by processing the files in RAM/Temp file then deleted immediately after finishing.
 *     Accuracy is improved by automatically upscaling the low-res images for better Arabic recognition.
 * </p>
 */

@Service
public class OcrService {

    /**
     * The extractText method takes a raw file upload processing it using Tesseract then returning the extracted text.
     * @param file the {@link MultipartFile} received from the browser.
     * @return A string containing the extracted Arabic Text
     */
    public String extractText(MultipartFile file){
        File tempFile = null;
        try{

            // STEP 1: here we convert RAM data to a physical file because Tesseract requires a physical file path.
            // So for privacy reasons we create a temp one.
            tempFile = File.createTempFile("upload", file.getOriginalFilename());
            try (FileOutputStream fos = new FileOutputStream(tempFile)){
                fos.write(file.getBytes());
            }

            // STEP 2: here we pre-process the image into memory to check the resolution.
            BufferedImage originalImage = ImageIO.read(tempFile);
            if(originalImage == null){
                return "Error: Could not read image file.";
            }

            // Tesseract usually works with scanned documents so it struggles with standard images.
            // The fix is upscaling the image by 3x to simulate a high quality scanned document.
            BufferedImage scaledImage = upscaleImage(originalImage, 3.0);

            //STEP 3: configuring and initializing Tesseract
            Tesseract tesseract = new Tesseract();
            tesseract.setDatapath("tessdata"); // Looks for 'tessdata' directory in the project root.
            tesseract.setLanguage("ara"); // Switches the language to Arabic

            // Telling Tesseract to assume that the file contains blocks of text instead of columns and segments.
            // That fixes the confusion Tesseract gets by trying to read documents with different text formats.
            tesseract.setPageSegMode(6);

            // STEP 4: Doing the OCR
            return tesseract.doOCR(scaledImage);
        } catch(Exception e){
            e.printStackTrace();
            return "Error: There was a problem during processing the image file: " + e.getMessage();
        } finally {

            // Privacy feature: Cleaning up
            // Here we ensure the temp file is deleted from the server's hard drive.
            if(tempFile != null && tempFile.exists()){
                tempFile.delete();
            }
        }
    }

    /**
     * upscaleImage method is a helper method that increases the image resolution based on a scaleFactor.
     * This makes Arabic's characters complex features such as dots and lines distinct enough for Tesseract.
     */
    private static BufferedImage upscaleImage(BufferedImage original, double scaleFactor){
        int newWidth = (int) (original.getWidth() * scaleFactor);
        int newHeight = (int) (original.getHeight() * scaleFactor);

        BufferedImage resized = new BufferedImage(newWidth, newHeight, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = resized.createGraphics();

        g.drawImage(original.getScaledInstance(newWidth, newHeight, Image.SCALE_SMOOTH), 0, 0, null);
        g.dispose();
        return resized;
    }
}

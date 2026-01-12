<?php

echo "Upload script was called";

$upload_dir = "upload_testing/";

$file = $_FILES["file"];

// TODO: Don't trust the file name given, rename it to the expected format
$original_name = basename($file["name"]);

$dest = $upload_dir . time() . "-" . $original_name;

if (move_uploaded_file($file["tmp_name"], $dest)) {
    echo "File uploaded successfully";
} else {
    echo "Upload failed";
}
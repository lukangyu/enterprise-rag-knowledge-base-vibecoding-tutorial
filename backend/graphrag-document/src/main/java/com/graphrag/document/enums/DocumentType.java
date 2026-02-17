package com.graphrag.document.enums;

import lombok.Getter;

import java.util.Arrays;
import java.util.Set;

@Getter
public enum DocumentType {
    PDF("pdf", Set.of("application/pdf")),
    WORD("docx", Set.of("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword")),
    MARKDOWN("md", Set.of("text/markdown", "text/x-markdown")),
    TXT("txt", Set.of("text/plain"));

    private final String extension;
    private final Set<String> mimeTypes;

    DocumentType(String extension, Set<String> mimeTypes) {
        this.extension = extension;
        this.mimeTypes = mimeTypes;
    }

    public static DocumentType getByExtension(String extension) {
        if (extension == null) {
            return null;
        }
        String ext = extension.toLowerCase().replace(".", "");
        return Arrays.stream(values())
                .filter(type -> type.extension.equals(ext))
                .findFirst()
                .orElse(null);
    }

    public static DocumentType getByMimeType(String mimeType) {
        if (mimeType == null) {
            return null;
        }
        return Arrays.stream(values())
                .filter(type -> type.mimeTypes.contains(mimeType.toLowerCase()))
                .findFirst()
                .orElse(null);
    }

    public static boolean isValidExtension(String extension) {
        return getByExtension(extension) != null;
    }

    public static boolean isValidMimeType(String mimeType) {
        return getByMimeType(mimeType) != null;
    }
}

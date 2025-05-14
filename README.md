# TwinCAT_To_PDF

> Automatically generates a clean, structured PDF from TwinCAT PLC source files (`.TcPOU`, `.TcDUT`, `.TcGVL`, `.TcIO`), with table of contents and syntax highlighting.

## 📜 Description

**TwinCAT_To_PDF** is a Python script designed to extract code from XML-based TwinCAT project files and generate a human-readable PDF document. It supports:

- Full code extraction: declarations, implementations, methods, and properties.
- Hierarchical structure with automatic section numbering.
- Table of contents for easy navigation.
- Syntax highlighting for better readability.

This tool is especially useful for documentation, archiving, or code reviews where a printable or shareable version of the PLC logic is required.

> ⚠️ **Note:** This tool only supports **Structured Text (ST)**. Other TwinCAT languages like LD, FBD, or SFC are not supported.

## 🗂️ Supported File Types

- `.TcPOU` – Function Blocks, Functions, Programs
- `.TcDUT` – Data Types
- `.TcGVL` – Global Variable Lists
- `.TcIO` – IO Configurations

## ✅ Features

- Extracts structured TwinCAT code from XML files
- Formats code with consistent indentation
- Highlights keywords and comments
- Automatically generates a PDF with:
  - Custom title page
  - Table of contents
  - Section headers based on file names
  - Page numbers and footer info

## 🚀 Getting Started

To generate a PDF from the XML files of your TwinCAT project, run the following command:

```bash
python TwinCAT_To_PDF.py /path/to/your/TwinCAT_project output_document.pdf
```
### Prerequisites
- Python 3.10+

# =============================================================================
# File Name      : TwinCAT_To_PDF.py
# Author         : Luca Freund
# Date           : 13.05.2025
# Description    : Python script to generate a structured PDF from TwinCAT 
#                  source files (.TcPOU, .TcDUT, etc.), with syntax highlighting 
#                  (types in blue, comments in green) and hierarchical 
#                  chapter numbering (1, 1.1, 1.1.1...).
# =============================================================================

import os
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

def extract_twincat_code(file_path):
    """Extract complete TwinCAT code including methods and properties from XML file."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Try to get object name and type
        obj_type = root.tag.split('}')[-1]  # Extract tag without namespace
        
        if obj_type == 'POU':
            obj_name = root.attrib.get('Name', 'Unknown')
            pou_type = root.attrib.get('SpecialFunc', '')
            title = f"{obj_type}: {obj_name} {pou_type}"
        elif obj_type == 'Itf':
            obj_name = root.attrib.get('Name', 'Unknown')
            title = f"Interface: {obj_name}"
        elif obj_type == 'DUT':
            obj_name = root.attrib.get('Name', 'Unknown')
            title = f"DUT: {obj_name}"
        elif obj_type == 'GVL':
            obj_name = root.attrib.get('Name', 'Unknown')
            title = f"GVL: {obj_name}"
        else:
            title = f"{Path(file_path).name}"
        
        # Collect all code segments
        code_segments = []
        
        # Get main declaration
        declaration = root.find(".//Declaration")
        if declaration is not None and declaration.text:
            cdata_content = extract_cdata(declaration.text)
            if cdata_content:
                code_segments.append(("Declaration", cdata_content))
        
        # Get implementation
        implementation = root.find(".//Implementation/ST")
        if implementation is not None and implementation.text:
            cdata_content = extract_cdata(implementation.text)
            if cdata_content:
                code_segments.append(("Implementation", cdata_content))
        
        # Get methods
        methods = root.findall(".//Method")
        for method in methods:
            method_name = method.attrib.get('Name', 'Unknown')
            method_decl = method.find("Declaration")
            method_impl = method.find("Implementation/ST")
            
            if method_decl is not None and method_decl.text:
                method_decl_content = extract_cdata(method_decl.text)
                if method_decl_content:
                    code_segments.append((f"Method {method_name} Declaration", method_decl_content))
            
            if method_impl is not None and method_impl.text:
                method_impl_content = extract_cdata(method_impl.text)
                if method_impl_content:
                    code_segments.append((f"Method {method_name} Implementation", method_impl_content))
        
        # Get properties
        properties = root.findall(".//Property")
        for prop in properties:
            prop_name = prop.attrib.get('Name', 'Unknown')
            prop_decl = prop.find("Declaration")
            
            if prop_decl is not None and prop_decl.text:
                prop_decl_content = extract_cdata(prop_decl.text)
                if prop_decl_content:
                    code_segments.append((f"Property {prop_name} Declaration", prop_decl_content))
            
            # Get and set methods
            get_method = prop.find("Get")
            set_method = prop.find("Set")
            
            if get_method is not None:
                get_decl = get_method.find("Declaration")
                get_impl = get_method.find("Implementation/ST")
                
                if get_decl is not None and get_decl.text:
                    get_decl_content = extract_cdata(get_decl.text)
                    if get_decl_content:
                        code_segments.append((f"Property {prop_name} Get Declaration", get_decl_content))
                
                if get_impl is not None and get_impl.text:
                    get_impl_content = extract_cdata(get_impl.text)
                    if get_impl_content:
                        code_segments.append((f"Property {prop_name} Get Implementation", get_impl_content))
            
            if set_method is not None:
                set_decl = set_method.find("Declaration")
                set_impl = set_method.find("Implementation/ST")
                
                if set_decl is not None and set_decl.text:
                    set_decl_content = extract_cdata(set_decl.text)
                    if set_decl_content:
                        code_segments.append((f"Property {prop_name} Set Declaration", set_decl_content))
                
                if set_impl is not None and set_impl.text:
                    set_impl_content = extract_cdata(set_impl.text)
                    if set_impl_content:
                        code_segments.append((f"Property {prop_name} Set Implementation", set_impl_content))
        
        return title, code_segments
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, None

def extract_cdata(text):
    """Extract content from CDATA section."""
    if text:
        cdata_pattern = r'<!\[CDATA\[(.*?)\]\]>'
        match = re.search(cdata_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # If no CDATA tags, return the text directly (sometimes TwinCAT files don't use CDATA)
        return text.strip()
    return None

def is_twincat_file(file_path):
    """Check if file is a TwinCAT PLC file."""
    extensions = ['.TcPOU', '.TcDUT', '.TcGVL', '.TcIO']
    return file_path.suffix in extensions

def collect_files(input_folder):
    """Collect all TwinCAT files and maintain folder structure."""
    files_by_folder = {}
    for root, _, files in os.walk(input_folder):
        for file in files:
            file_path = Path(root) / file
            if is_twincat_file(file_path):
                relative_path = file_path.relative_to(input_folder)
                folder_path = relative_path.parent
                if folder_path not in files_by_folder:
                    files_by_folder[folder_path] = []
                files_by_folder[folder_path].append(file_path)
    return files_by_folder

def generate_pdf(code_files_by_folder, output_pdf):
    """Generate PDF from the extracted code files."""
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CodeStyle',
        fontName='Courier',
        fontSize=7,
        leading=10,
        spaceAfter=0,
        spaceBefore=0
    ))
    
    styles.add(ParagraphStyle(
        name='Heading',
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=12,
        spaceBefore=6,
        textColor=colors.black
    ))
    
    styles.add(ParagraphStyle(
        name='Subheading',
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceAfter=6,
        spaceBefore=6,
        textColor=colors.black
    ))

    title_style = ParagraphStyle(
        name='Title',
        fontName='Helvetica-Bold',
        fontSize=24,
        alignment=1,  # Center
        spaceAfter=30,
        textColor=colors.black
    )
    
    elements = []
    
    # Add title page
    elements.append(Spacer(1, 5*cm))
    elements.append(Paragraph("TwinCAT PLC PDF Auto-Gen", title_style))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(f"Generated on: {os.path.basename(os.path.dirname(output_pdf))}", 
                             styles['Normal']))
    elements.append(Paragraph(f"Total files: {len(code_files_by_folder)}", styles['Normal']))
    elements.append(PageBreak())
    
    # Add table of contents
    elements.append(Paragraph("Table of Contents", styles['Heading']))
    elements.append(Spacer(1, 0.5*cm))
    

    toc_data = []
    
    def add_to_toc(data, prefix=""):
        """Recursive function to add items to the Table of Contents."""
        for idx, (folder, files) in enumerate(data.items()):
            folder_label = f"{prefix}{idx + 1}"  # Add numbering for this folder level
            toc_data.append([f"{folder_label} {folder}"])
            
            file_index = 1
            for title, _ in files:
                toc_data.append([f"    {folder_label}.{file_index} {title}"])
                file_index += 1
            
            # Recursively go deeper if there are subfolders
            subfolder_index = 1
            for subfolder, subfiles in data.items():
                if isinstance(subfiles, dict):  # Only handle subfolders
                    add_to_toc({subfolder: subfiles}, f"{folder_label}.{subfolder_index}")
                    subfolder_index += 1

    add_to_toc(code_files_by_folder)  # Generate table of contents
    toc = Table(toc_data, colWidths=[450])
    toc.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                             ('FONTSIZE', (0,0), (-1,-1), 10),
                             ('LEADING', (0,0), (-1,-1), 14)]))
    elements.append(toc)
    elements.append(PageBreak())
    
    # Add each code file organized by folder
    def add_code_files(data, prefix=""):
        """Recursive function to add code files to the PDF."""
        FirstCycleDone=0
        for idx, (folder, files) in enumerate(data.items()):
            if FirstCycleDone:
                elements.append(PageBreak()) 
            FirstCycleDone=1
            folder_label = f"{prefix}{idx + 1}"  # Add numbering for this folder level
            elements.append(Paragraph(f"{folder_label} {folder}", styles['Heading']))
            
            file_index = 1
            for title, code_segments in files:
                elements.append(Paragraph(f"{folder_label}.{file_index} {title}", styles['Subheading']))
                for segment_title, code in code_segments:
                    elements.append(Paragraph(segment_title, styles['Subheading']))
                    code_lines = code.split('\n')
                    for line in code_lines:
                        safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        if safe_line.strip():
                           keywords = [
                                '__UXINT', '__XINT', '__XWORD', 'BIT', 'BOOL', 'BYTE', 'DATE', 'DATE_AND_TIME',
                                'DINT', 'DT', 'DWORD', 'INT', 'LDATE', 'LDATE_AND_TIME', 'LDT', 'LINT',
                                'LREAL', 'LTIME', 'LTOD', 'LWORD', 'REAL', 'SINT', 'STRING', 'TIME',
                                'TOD', 'TIME_OF_DAY', 'UDINT', 'UINT', 'ULINT', 'USINT', 'WORD', 'WSTRING',
                                'FUNCTION_BLOCK', 'PROGRAM', 'IMPLEMENTS', 'INTERFACE', 'VAR', 'END_VAR', 'EXTENDS',
                                'PROPERTY', 'TYPE', 'END_TYPE', 'STRUCT', 'END_STRUCT', 'POINTER', 'TO', 'DO',
                                'FOR', 'END_FOR', 'END_IF', 'IF', 'AND', 'AND_THEN', 'OR_ELSE', 'ELSE', 'WHILE',
                                'REPEAT', 'UNTIL', 'CASE', 'OF', 'ADR', 'XOR', 'VAR_INPUT', 'VAR_OUTPUT', 'PERSISTENT',
                                'RETAIN', 'AT', 'ARRAY', 'OF', 'METHOD', 'THIS^', 'NOT', 'THEN', 'ELSIF',
                                'REFERENCE', 'REF=', 'PUBLIC', 'PRIVATE', 'CONSTANT', 'VAR_GLOBAL'
                           ]   
                           if "//" in line:
                                code_part, comment_part = line.split("//", 1)
                                for keyword in keywords:
                                    code_part = re.sub(
                                        rf'\b{keyword}\b',
                                        lambda m: f'<font color="blue">{m.group(0)}</font>',
                                        code_part
                                    )
                                full_line = code_part + f'<font color="green">//{comment_part}</font>'
                                elements.append(Paragraph(full_line.strip(), styles['CodeStyle']))
                           else:
                                highlighted = safe_line
                                for keyword in keywords:
                                    highlighted = re.sub(
                                        rf'\b{keyword}\b',
                                        lambda m: f'<font color="blue">{m.group(0)}</font>',
                                        highlighted
                                    )
 
                                elements.append(Paragraph(highlighted.strip(), styles['CodeStyle']))
                        else:
                            elements.append(Spacer(1, 10))
                    elements.append(Spacer(1, 0.5*cm))
                file_index += 1
            
            subfolder_index = 1
            for subfolder, subfiles in data.items():
                if isinstance(subfiles, dict): 
                    add_code_files({subfolder: subfiles}, f"{folder_label}.{subfolder_index}")
                    subfolder_index += 1
    
    add_code_files(code_files_by_folder)  # Add the actual code files
    doc.build(elements)
    print(f"PDF generated successfully: {output_pdf}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python twincat_code_extractor.py <input_folder> <output_pdf>")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_pdf = sys.argv[2]
    
    # Collect all TwinCAT files by folder
    code_files_by_folder = collect_files(input_folder)
    
    print(f"Found {sum(len(files) for files in code_files_by_folder.values())} TwinCAT files")
    
    # Extract code from files
    for folder, files in code_files_by_folder.items():
        for i, file_path in enumerate(files):
            title, code_segments = extract_twincat_code(file_path)
            if title and code_segments:
                files[i] = (title, code_segments)
    
    # Generate PDF with folder structure
    generate_pdf(code_files_by_folder, output_pdf)

if __name__ == "__main__":
    main()
#!/bin/bash

# Указываем путь к папке с SVG-файлами
INPUT_FOLDER="media/pass_result"

# Находим все SVG-файлы в указанной папке и её подкаталогах
find "$INPUT_FOLDER" -type f -name "*.svg" | while read svg_file; do
    # Определяем имя PNG-файла на основе имени SVG-файла
    png_filename="${svg_file%.*}.png"
    
    # Экспортируем SVG в PNG с помощью Inkscape
    inkscape -z --export-png="$png_filename" --export-dpi=300 "$svg_file"
    
    echo "Exported $svg_file to $png_filename"
done


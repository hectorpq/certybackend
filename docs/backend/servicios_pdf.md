# Servicio: Generación de PDFs

La generación de los certificados en formato PDF se realiza utilizando la biblioteca **ReportLab**.

## Funcionamiento

El método `certificate.generate()` es el punto de entrada para la creación de un PDF.

1.  **Invoca a `PDFService`**: Este servicio centraliza la lógica de creación del PDF.
2.  **Carga de Plantilla**: Se utiliza la imagen de fondo (`background_image`) de la `Template` asociada.
3.  **Renderizado de Texto**:
    - El nombre del participante se posiciona en el lienzo según las coordenadas (`x_coord`, `y_coord`) y los estilos (fuente, tamaño, color) definidos en la `Template`.
    - El `layout_config` de la plantilla permite añadir otros elementos dinámicos, como la firma del instructor.
4.  **Guardado**: El archivo PDF generado se guarda en el directorio de medios y la ruta se almacena en el campo `pdf_url` del certificado.

## Lógica de Negocio

- Un PDF solo se puede generar si el certificado está en estado `pending`.
- Por defecto, se valida que el participante tenga `attendance = True` en la inscripción (`Enrollment`) antes de generar el certificado.
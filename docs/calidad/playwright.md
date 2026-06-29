# Pruebas End-to-End (E2E) con Playwright

Para garantizar la calidad y el correcto funcionamiento de los flujos de usuario completos, el proyecto utiliza Playwright para las pruebas End-to-End.

## ¿Qué es Playwright?

Playwright es un framework de automatización de navegadores desarrollado por Microsoft. Permite escribir pruebas que simulan las acciones de un usuario real en un navegador (Chrome, Firefox, Safari).

## Flujos de Prueba Clave

Las pruebas E2E se centran en los caminos críticos de la aplicación:

1.  **Flujo de Autenticación**: Probar el login, el logout y la protección de rutas.
2.  **Creación de un Evento**: Simular la creación de un evento desde el formulario hasta su aparición en la lista.
3.  **Generación de un Certificado Individual**: Probar el flujo completo de crear un participante, un evento, inscribirlo y generar su certificado.
4.  **Flujo de Carga Masiva**: Probar la subida de un archivo Excel, la previsualización y la confirmación de la generación.
5.  **Verificación Pública**: Probar que un código de verificación válido muestra la información correcta en la página pública.
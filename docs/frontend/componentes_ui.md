# Componentes UI — `src/components/ui/`

Librería de componentes atómicos reutilizables construidos con TailwindCSS.

| Componente | Archivo | Props principales |
|------------|---------|-------------------|
| **Button** | `Button.tsx` | `variant` (primary/secondary/danger), `size`, `loading`, `disabled` |
| **Input** | `Input.tsx` | `label`, `error`, `type`, `placeholder` |
| **Select** | `Select.tsx` | `label`, `options`, `error`, `placeholder` |
| **Textarea** | `Textarea.tsx` | `label`, `error`, `rows` |
| **Modal** | `Modal.tsx` | `isOpen`, `onClose`, `title`, `size` (sm/md/lg) |
| **Card** | `Card.tsx` | `title`, `children`, `className` |
| **Badge** | `Badge.tsx` | `variant` (success/warning/danger/info), `children` |
| **Pagination** | `Pagination.tsx` | `currentPage`, `totalPages`, `onPageChange` |
| **SearchInput** | `SearchInput.tsx` | `value`, `onChange`, `placeholder` |
| **FileUpload** | `FileUpload.tsx` | `accept`, `onFileSelect`, `maxSizeMB`, `label` |
| **Alert** | `Alert.tsx` | `variant` (success/error/warning/info), `message`, `onClose` |
| **Spinner** | `Spinner.tsx` | `size` (sm/md/lg) |
| **PageLoader** | `Spinner.tsx` | Loader de pantalla completa con overlay |
| **SignaturePad** | `SignaturePad.tsx` | `onSave`, `width`, `height`, `label` |

## Componentes de Layout

| Componente | Ruta | Descripción |
|------------|------|-------------|
| **Layout** | `components/layout/Layout.tsx` | Shell principal: Sidebar + `<Outlet />` |
| **Sidebar** | `components/layout/Sidebar.tsx` | Navegación lateral colapsable con avatar y logout |

import '@testing-library/jest-dom/vitest'

URL.createObjectURL = () => 'blob:preview'
URL.revokeObjectURL = () => {}
Element.prototype.scrollIntoView = () => {}

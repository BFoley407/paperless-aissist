export function buildPaperlessDocumentUrl(
  paperlessUrl: string | null | undefined,
  documentId: number | null | undefined,
): string | null {
  if (!paperlessUrl || documentId === null || documentId === undefined) {
    return null
  }

  return `${paperlessUrl.replace(/\/+$/, '')}/documents/${documentId}`
}

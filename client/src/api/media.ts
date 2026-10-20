import { api, ApiError } from '../lib/api'

/** Image affichable. `url` n'est servie qu'à ceux qui ont le droit de voir son contenu. */
export type Photo = { url: string; width: number; height: number }

/** Image tout juste envoyée : `id` sert à la rattacher à un post ou à une communauté. */
export type UploadedImage = Photo & { id: number }

/** photo : photo d'un post ; banner / icon : visuels d'une communauté (écran 15). */
export type UploadKind = 'photo' | 'banner' | 'icon'

/** Mêmes limites que l'API, vérifiées avant l'envoi pour répondre tout de suite. */
export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
export const UPLOAD_MAX_MB = 10

export const mediaApi = {
  upload: (file: File, kind: UploadKind) => {
    if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
      return Promise.reject(
        new ApiError(422, { code: 'invalid_image', message: 'Choisissez une image JPEG, PNG ou WebP.' }),
      )
    }
    if (file.size > UPLOAD_MAX_MB * 1024 * 1024) {
      return Promise.reject(
        new ApiError(413, { code: 'file_too_large', message: `Image trop lourde (${UPLOAD_MAX_MB} Mo max.).` }),
      )
    }
    const form = new FormData()
    form.append('file', file)
    form.append('kind', kind)
    return api<UploadedImage>('/uploads', { method: 'POST', body: form })
  },
}

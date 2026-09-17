import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import {
  UploadCloud,
  Image as ImageIcon,
  X,
  Plus,
  ShieldAlert,
  ArrowRight,
  Info,
  Check,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { createInspection, uploadImages } from '@/services/api'
import type { ImageType } from '@/types'

interface UploadedImageFile {
  file: File
  preview: string
  image_type: ImageType
}

const CATEGORIES = [
  'Food & Beverages',
  'Edible Oils & Fats',
  'Spices & Condiments',
  'Biscuits & Confectionery',
  'Cosmetics & Personal Care',
  'Detergents & Soaps',
  'Pharmaceuticals',
  'Paints & Varnishes',
  'Hardware & Electrical',
  'General Packaged Goods',
]

export default function NewInspectionPage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState(CATEGORIES[0])
  const [images, setImages] = useState<UploadedImageFile[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newItems = acceptedFiles.map((file, idx) => {
      let defaultType: ImageType = 'front'
      if (idx === 1) defaultType = 'back'
      else if (idx === 2) defaultType = 'side'
      else if (idx > 2) defaultType = 'label'

      return {
        file,
        preview: URL.createObjectURL(file),
        image_type: defaultType,
      }
    })
    setImages((prev) => [...prev, ...newItems])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp'],
    },
    maxSize: 20 * 1024 * 1024,
  })

  const removeImage = (index: number) => {
    setImages((prev) => {
      const copy = [...prev]
      URL.revokeObjectURL(copy[index].preview)
      copy.splice(index, 1)
      return copy
    })
  }

  const updateImageType = (index: number, type: ImageType) => {
    setImages((prev) => {
      const copy = [...prev]
      copy[index].image_type = type
      return copy
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) {
      setError('Please provide a product title or trade description.')
      return
    }
    if (images.length === 0) {
      setError('Please upload at least one image (front/back/label) to proceed with OCR.')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      // 1. Create inspection
      let inspectionId = 'insp-' + Date.now().toString(36)
      try {
        const insp = await createInspection({
          title,
          description,
          product_category: category,
        })
        inspectionId = insp.id
        // 2. Upload images to backend
        await uploadImages(
          inspectionId,
          images.map((img) => ({ file: img.file, image_type: img.image_type }))
        )
      } catch (backendErr) {
        console.warn('Backend unavailable, proceeding in demo mode with ID:', inspectionId)
      }

      // Navigate to processing pipeline
      navigate(`/inspections/${inspectionId}/processing`, {
        state: {
          title,
          category,
          imagePreviews: images.map((i) => ({ preview: i.preview, type: i.image_type, name: i.file.name })),
        },
      })
    } catch (err: any) {
      setError(err.message || 'Failed to initialize inspection.')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Create New Packaging Inspection
        </h1>
        <p className="text-sm text-slate-500">
          Upload product images for automated OCR declaration extraction and Legal Metrology rule verification.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-center gap-3 text-sm">
          <ShieldAlert className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="shadow-xs">
          <CardHeader>
            <CardTitle className="text-base">Product Information</CardTitle>
            <CardDescription>
              Basic metadata recorded for the enforcement docket
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Product Name / Trade Description <span className="text-red-500">*</span>
              </label>
              <Input
                placeholder="e.g. Parle-G Gluco Biscuits 250g or Haldiram's Bhujia Sev"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Commodity Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-[#1e3a5f]"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Applicable Standard
                </label>
                <div className="h-9 flex items-center px-3 rounded-md border border-slate-200 bg-slate-50 text-xs text-slate-600 font-medium">
                  LM(PC) Rules, 2011 (as amended)
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Inspection Context / Retailer Notes
              </label>
              <textarea
                rows={2}
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-[#1e3a5f]"
                placeholder="e.g. Sample seized from Big Mart Retail Outlet, Sector 12, Batch sampled for mandatory declarations check."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Image Upload Area */}
        <Card className="shadow-xs">
          <CardHeader>
            <CardTitle className="text-base">Packaging Images (Multi-view)</CardTitle>
            <CardDescription>
              Upload high-resolution front, back, and side panel photographs. Clear lighting ensures accurate OCR text and bounding-box detection.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-blue-500 bg-blue-50/50'
                  : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
              }`}
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center justify-center gap-2">
                <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-[#1e3a5f]">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <p className="font-medium text-slate-800 text-sm">
                  Drag &amp; drop product images here, or <span className="text-blue-600 underline">browse files</span>
                </p>
                <p className="text-xs text-slate-500">
                  Supports JPEG, PNG, WEBP (Max 20MB per image)
                </p>
              </div>
            </div>

            {/* Image Previews List */}
            {images.length > 0 && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Selected Packaging Panels ({images.length})
                  </h4>
                  <span className="text-[11px] text-slate-400">
                    Label panels properly to guide rule mapping
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {images.map((item, idx) => (
                    <div
                      key={idx}
                      className="relative border border-slate-200 rounded-lg overflow-hidden bg-white shadow-xs group"
                    >
                      <div className="h-40 bg-slate-100 flex items-center justify-center overflow-hidden">
                        <img
                          src={item.preview}
                          alt={`Panel ${idx + 1}`}
                          className="w-full h-full object-contain"
                        />
                      </div>

                      <button
                        type="button"
                        onClick={() => removeImage(idx)}
                        className="absolute top-2 right-2 w-7 h-7 rounded-full bg-black/70 text-white flex items-center justify-center hover:bg-red-600 transition-colors cursor-pointer"
                        title="Remove image"
                      >
                        <X className="w-4 h-4" />
                      </button>

                      <div className="p-3 bg-white space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-slate-700 truncate max-w-[120px]">
                            {item.file.name}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            {(item.file.size / 1024 / 1024).toFixed(1)} MB
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <label className="text-[10px] text-slate-500 font-semibold">Panel:</label>
                          <select
                            value={item.image_type}
                            onChange={(e) => updateImageType(idx, e.target.value as ImageType)}
                            className="text-xs border border-slate-200 rounded px-1.5 py-0.5 bg-slate-50 text-slate-800 flex-1 focus:outline-none"
                          >
                            <option value="front">Front Panel (Principal)</option>
                            <option value="back">Back Panel (Declarations)</option>
                            <option value="side">Side Panel</option>
                            <option value="top">Top Flap</option>
                            <option value="bottom">Bottom Panel</option>
                            <option value="label">Nutritional / Additional Label</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
          <CardFooter className="flex justify-between items-center bg-slate-50 border-t border-slate-200 p-4">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Info className="w-4 h-4 text-slate-400" />
              <span>Multi-view processing combines declarations across all package facets</span>
            </div>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="bg-[#1e3a5f] hover:bg-[#153e75] text-white flex items-center gap-2 cursor-pointer"
            >
              {isSubmitting ? (
                <>Initiating Pipeline...</>
              ) : (
                <>
                  Start Inspection <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  )
}

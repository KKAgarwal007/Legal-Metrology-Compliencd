import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import DashboardPage from './pages/DashboardPage'
import NewInspectionPage from './pages/NewInspectionPage'
import InspectionListPage from './pages/InspectionListPage'
import InspectionDetailPage from './pages/InspectionDetailPage'
import ProcessingPage from './pages/ProcessingPage'
import RegulationsPage from './pages/RegulationsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="inspections/new" element={<NewInspectionPage />} />
          <Route path="inspections" element={<InspectionListPage />} />
          <Route path="inspections/:id" element={<InspectionDetailPage />} />
          <Route path="inspections/:id/processing" element={<ProcessingPage />} />
          <Route path="regulations" element={<RegulationsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

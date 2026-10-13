import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Overview from './pages/Overview'
import MedicineSearch from './pages/MedicineSearch'
import ManufacturerInsights from './pages/ManufacturerInsights'
import SavingsExplorer from './pages/SavingsExplorer'
import SafetyInsights from './pages/SafetyInsights'
import Insights from './pages/Insights'
import SqlTransparency from './pages/SqlTransparency'
import ChartInsights from './pages/ChartInsights'

export default function App() {
  return <Layout><Routes>
    <Route path="/" element={<Overview />} />
    <Route path="/search" element={<MedicineSearch />} />
    <Route path="/manufacturers" element={<ManufacturerInsights />} />
    <Route path="/savings" element={<SavingsExplorer />} />
    <Route path="/safety" element={<SafetyInsights />} />
    <Route path="/insights" element={<Insights />} />
    <Route path="/chart-insights" element={<ChartInsights />} />
    <Route path="/sql" element={<SqlTransparency />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></Layout>
}

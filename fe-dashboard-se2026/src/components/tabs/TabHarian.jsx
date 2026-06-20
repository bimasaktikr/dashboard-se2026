import { TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function TabHarian({ chartData }) {
  return (
    <div className="p-2">
      <h2 className="text-xl font-bold mb-6 text-white flex items-center gap-2">
        <TrendingUp className="text-indigo-400" size={22} /> Grafik Linimasa Kecepatan Enumerasi Lapangan SE2026
      </h2>
      
      {chartData.length === 0 ? (
        <div className="text-center py-12 text-slate-500 font-mono">Belum ada data sejarah historis di tanggal terpilih.</div>
      ) : (
        <div className="w-full h-[400px] bg-slate-900/50 p-4 border border-slate-700/40 rounded-xl shadow-inner">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="tanggal" stroke="#94a3b8" fontClassName="font-mono text-xs" />
              <YAxis stroke="#94a3b8" fontClassName="font-mono text-xs" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569', borderRadius: '10px', color: '#fff' }} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              <Line type="monotone" dataKey="Selesai" stroke="#10b981" strokeWidth={3} activeDot={{ r: 8 }} name="Kuesioner Masuk (Submitted)" />
              <Line type="monotone" dataKey="Terbuka_Open" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" name="Beban Tersisa (Open)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
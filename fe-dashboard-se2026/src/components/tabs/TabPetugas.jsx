import { useState } from 'react';
import { ChevronDown, ChevronUp, Map, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

// Tambahkan prop dataTimeline yang baru saja kita lempar dari App.jsx
export default function TabPetugas({ dataPetugas, dataTimeline }) {
  const [expandedRow, setExpandedRow] = useState(null);

  const toggleRow = (email) => {
    setExpandedRow(expandedRow === email ? null : email);
  };

  // Fungsi dinamis untuk membuat grafik khusus petugas yang sedang di-klik
  const getChartDataForPetugas = (email) => {
    if (!dataTimeline) return [];
    
    // 1. Ambil data historis hanya untuk email petugas ini
    const filtered = dataTimeline.filter(d => d.email_petugas === email);
    
    // 2. Gabungkan jika dalam 1 hari dia mengerjakan lebih dari 1 wilayah
    const grouped = {};
    filtered.forEach(d => {
      if (!grouped[d.tanggal]) grouped[d.tanggal] = { tanggal: d.tanggal, Selesai: 0, Sisa: 0 };
      grouped[d.tanggal].Selesai += d.selesai;
      grouped[d.tanggal].Sisa += d.sisa;
    });

    // 3. Kembalikan dalam bentuk Array untuk Recharts
    return Object.values(grouped).sort((a, b) => a.tanggal.localeCompare(b.tanggal));
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-700 text-slate-400 text-sm uppercase font-semibold">
            <th className="p-4 w-10"></th>
            <th className="p-4">Nama Petugas</th>
            <th className="p-4 text-center">Beban Target</th>
            <th className="p-4 text-center">Selesai (Sub)</th>
            <th className="p-4 text-center">Sisa (Open)</th>
            <th className="p-4 w-1/4">Capaian Kinerja Total</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/50 text-slate-300">
          {dataPetugas.map((item, idx) => (
            <>
              {/* BARIS UTAMA (BISA DI-KLIK) */}
              <tr 
                key={idx} 
                onClick={() => toggleRow(item.email)}
                className="hover:bg-slate-700/50 transition-colors cursor-pointer"
              >
                <td className="p-4 text-slate-400">
                  {expandedRow === item.email ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </td>
                <td className="p-4">
                  <div className="font-bold text-white flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-400"></span> {item.nama}
                  </div>
                  <div className="text-slate-400 font-mono text-xs mt-1">{item.email} • {item.role}</div>
                </td>
                <td className="p-4 text-center font-mono">{item.target}</td>
                <td className="p-4 text-center font-mono text-green-400">{item.selesai}</td>
                <td className="p-4 text-center font-mono text-amber-400">{item.sisa}</td>
                <td className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-full bg-slate-700 rounded-full h-3.5 border border-slate-600 overflow-hidden">
                      <div className="bg-gradient-to-r from-purple-500 to-indigo-500 h-full rounded-full transition-all duration-500" style={{ width: `${item.progres_persen}%` }}></div>
                    </div>
                    <span className="text-sm font-bold text-white font-mono w-12 text-right">{item.progres_persen}%</span>
                  </div>
                </td>
              </tr>

              {/* SUB-BARIS AKORDEON (MUNCUL JIKA DI-EXPAND) */}
              {expandedRow === item.email && (
                <tr className="bg-slate-900/80 border-l-2 border-indigo-500">
                  <td colSpan="6" className="p-4">
                    {/* MEMBAGI LAYAR MENJADI DUA KOLOM (GRID) */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pl-12 pr-4 py-2">
                      
                      {/* KOLOM KIRI: TABEL DETAIL ASSIGNMENT */}
                      <div>
                        <h4 className="text-xs font-bold text-indigo-400 uppercase flex items-center gap-2 mb-3">
                          <Map size={14} /> Detail Penugasan Region (SLS):
                        </h4>
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-slate-500 border-b border-slate-700/50">
                              <th className="pb-2 text-left">Kode Assignment</th>
                              <th className="pb-2 text-center">Target</th>
                              <th className="pb-2 text-center text-green-400">Selesai</th>
                              <th className="pb-2 text-center text-amber-400">Sisa</th>
                              <th className="pb-2 w-20 text-right">Progres</th>
                            </tr>
                          </thead>
                          <tbody>
                            {item.detail_assignment.map((assign, i) => (
                              <tr key={i} className="border-b border-slate-700/30 last:border-0 hover:bg-slate-800/40">
                                <td className="py-2 text-indigo-200 font-mono text-xs">{assign.assignment_code}</td>
                                <td className="py-2 text-center font-mono text-slate-400">{assign.target}</td>
                                <td className="py-2 text-center font-mono text-green-500/80">{assign.selesai}</td>
                                <td className="py-2 text-center font-mono text-amber-500/80">{assign.sisa}</td>
                                <td className="py-2 text-right font-mono font-bold text-indigo-300">{assign.progres_lokal}%</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* KOLOM KANAN: MINI CHART TREN HARIAN */}
                      <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800">
                        <h4 className="text-xs font-bold text-emerald-400 uppercase flex items-center gap-2 mb-4">
                          <TrendingUp size={14} /> Kecepatan Enumerasi Harian ({item.nama})
                        </h4>
                        <div className="w-full h-[180px]">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={getChartDataForPetugas(item.email)}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                              <XAxis dataKey="tanggal" stroke="#64748b" fontSize={10} tickMargin={10} />
                              <YAxis stroke="#64748b" fontSize={10} width={30} />
                              <Tooltip 
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }}
                                itemStyle={{ color: '#10b981' }}
                              />
                              <Line 
                                type="monotone" 
                                dataKey="Selesai" 
                                stroke="#10b981" 
                                strokeWidth={2} 
                                dot={{ r: 3, fill: '#10b981' }} 
                                name="Submitted"
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                    </div>
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}
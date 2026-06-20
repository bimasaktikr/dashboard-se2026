export default function TabDesa({ dataDesa }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-700 text-slate-400 text-sm uppercase font-semibold">
            <th className="p-4">Kecamatan</th>
            <th className="p-4">Kelurahan / Desa</th>
            <th className="p-4 text-center">Target</th>
            <th className="p-4 text-center">Selesai</th>
            <th className="p-4 text-center">Sisa</th>
            <th className="p-4 w-1/4">Progress Bar</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/50 text-slate-300">
          {dataDesa.map((item, idx) => (
            <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
              <td className="p-4 font-medium text-white">{item.kecamatan}</td>
              <td className="p-4">{item.desa}</td>
              <td className="p-4 text-center font-mono">{item.target}</td>
              <td className="p-4 text-center font-mono text-green-400">{item.selesai}</td>
              <td className="p-4 text-center font-mono text-amber-400">{item.sisa}</td>
              <td className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-full bg-slate-700 rounded-full h-3.5 border border-slate-600 overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-500 to-green-500 h-full rounded-full transition-all duration-500" style={{ width: `${item.progres_persen}%` }}></div>
                  </div>
                  <span className="text-sm font-bold text-white font-mono w-12 text-right">{item.progres_persen}%</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
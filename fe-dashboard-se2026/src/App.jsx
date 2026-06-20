import { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import DashboardCard from './components/DashboardCard';
import { Users, Filter, Layers, TrendingUp } from 'lucide-react';
// IMPORT KOMPONEN TAB MODULAR ANDA
import TabDesa from './components/tabs/TabDesa';
import TabPetugas from './components/tabs/TabPetugas';
import TabHarian from './components/tabs/TabHarian';

function App() {
  const [activeTab, setActiveTab] = useState('desa');
  const [dataDesa, setDataDesa] = useState([]);
  const [dataPetugas, setDataPetugas] = useState([]);
  const [dataTimeline, setDataTimeline] = useState([]); // State Linimasa Baru

  // State untuk Menyimpan Pilihan Filter
  const [selectedKecamatan, setSelectedKecamatan] = useState('');
  const [selectedKelurahan, setSelectedKelurahan] = useState('');

  // ==========================================
  // 1. DATA FETCHING FROM GERBANG API
  // ==========================================
  useEffect(() => {
    Promise.all([
      axios.get('api-se2026.bpskotamalang.id/api/v1/dashboard/summary'),
      axios.get('api-se2026.bpskotamalang.id/api/v1/dashboard/petugas'),
      axios.get('api-se2026.bpskotamalang.id/api/v1/dashboard/timeline') // Tarik data sejarah harian
    ])
    .then(([resDesa, resPetugas, resTimeline]) => {
      setDataDesa(resDesa.data.data);
      setDataPetugas(resPetugas.data.data);
      setDataTimeline(resTimeline.data.data);
    })
    .catch(err => console.error("Gagal koordinasi data dengan server:", err));
  }, []);

  // ==========================================
  // 2. LOGIKA GENERATE LIST EXTRACT FILTER
  // ==========================================
  // Ambil daftar unik kecamatan untuk dropdown pertama
  const listKecamatan = useMemo(() => {
    const unik = new Set(dataDesa.map(item => item.kecamatan));
    return Array.from(unik).sort();
  }, [dataDesa]);

  // Ambil daftar unik kelurahan berdasarkan kecamatan yang sedang dipilih (Dependent)
  const listKelurahan = useMemo(() => {
    if (!selectedKecamatan) return [];
    const filtered = dataDesa.filter(item => item.kecamatan === selectedKecamatan);
    const unik = new Set(filtered.map(item => item.desa));
    return Array.from(unik).sort();
  }, [dataDesa, selectedKecamatan]);

  // Reset filter kelurahan jika kecamatan diubah
  const handleKecamatanChange = (e) => {
    setSelectedKecamatan(e.target.value);
    setSelectedKelurahan('');
  };

  // ==========================================
  // 3. REACTIVE FILTERING ENGINE (MENGARUH KE SEMUA TAB)
  // ==========================================
  // Filter Tab 1: Data Desa
  const filteredDataDesa = useMemo(() => {
    return dataDesa.filter(item => {
      const matchKec = selectedKecamatan ? item.kecamatan === selectedKecamatan : true;
      const matchKel = selectedKelurahan ? item.desa === selectedKelurahan : true;
      return matchKec && matchKel;
    });
  }, [dataDesa, selectedKecamatan, selectedKelurahan]);

  // ==========================================
  // REACTIVE FILTERING ENGINE FOR TAB 2 (PETUGAS)
  // ==========================================
  const filteredDataPetugas = useMemo(() => {
    const filteredRaw = dataPetugas.filter(item => {
      const matchKec = selectedKecamatan ? item.kecamatan === selectedKecamatan : true;
      const matchKel = selectedKelurahan ? item.desa === selectedKelurahan : true;
      return matchKec && matchKel;
    });

    const aggregated = {};
    filteredRaw.forEach(item => {
      if (!aggregated[item.email]) {
        aggregated[item.email] = {
          nama: item.nama, email: item.email, role: item.role,
          target: 0, selesai: 0, sisa: 0,
          detail_assignment: [] // 🌟 WADAH BARU KHUSUS DETAIL ASSIGNMENT/SLS
        };
      }
      // Akumulasi Baris Utama Petugas
      aggregated[item.email].target += item.target;
      aggregated[item.email].selesai += item.selesai;
      aggregated[item.email].sisa += item.sisa;
      
      // 🌟 DORONG DATA ASSIGNMENT (REGION CODE) KE DALAM KANTONG RINCIAN
      aggregated[item.email].detail_assignment.push({
        assignment_code: item.assignment_code,
        desa: item.desa,
        target: item.target,
        selesai: item.selesai,
        sisa: item.sisa,
        progres_lokal: item.target > 0 ? Number((item.selesai / item.target * 100).toFixed(2)) : 0
      });
    });

    return Object.values(aggregated).map(p => ({
      ...p,
      progres_persen: p.target > 0 ? Number((p.selesai / p.target * 100).toFixed(2)) : 0
    }));
  }, [dataPetugas, selectedKecamatan, selectedKelurahan]);

  // ==========================================
  // REACTIVE FILTERING ENGINE FOR TAB 3 (HARIAN)
  // ==========================================
  const chartDataHarian = useMemo(() => {
    // Saring data mentah timeline berdasarkan filter area terpilih
    const filteredTimeline = dataTimeline.filter(item => {
      const matchKec = selectedKecamatan ? item.kecamatan === selectedKecamatan : true;
      const matchKel = selectedKelurahan ? item.desa === selectedKelurahan : true;
      return matchKec && matchKel;
    });

    // Satukan dan akumulasikan data jika dikelompokkan berdasarkan tanggal unik
    const groupByDate = {};
    filteredTimeline.forEach(item => {
      if (!groupByDate[item.tanggal]) {
        groupByDate[item.tanggal] = { tanggal: item.tanggal, Selesai: 0, Terbuka_Open: 0 };
      }
      groupByDate[item.tanggal].Selesai += item.selesai;
      groupByDate[item.tanggal].Terbuka_Open += item.sisa;
    });

    // Kembalikan array urut kronologis tanggal untuk Recharts
    return Object.values(groupByDate);
  }, [dataTimeline, selectedKecamatan, selectedKelurahan]);

  // ==========================================
  // 4. DYNAMIC RE-CALCULATE KPI STATS
  // ==========================================
  const globalStats = useMemo(() => {
    const target = filteredDataDesa.reduce((acc, curr) => acc + curr.target, 0);
    const selesai = filteredDataDesa.reduce((acc, curr) => acc + curr.selesai, 0);
    const sisa = filteredDataDesa.reduce((acc, curr) => acc + curr.sisa, 0);
    return { target, selesai, sisa };
  }, [filteredDataDesa]);


  return (
    <div className="p-8 min-h-screen bg-slate-900 text-slate-100 font-sans">
      
      {/* HEADER COMMAND CENTER */}
      <header className="mb-8 flex justify-between items-center border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">COMMAND CENTER SE2026</h1>
          <p className="text-slate-400 mt-1">BPS Kota Malang — Sistem Monitoring Progress Unggulan</p>
        </div>
        <div className="bg-slate-800 px-4 py-2 rounded-xl border border-slate-700 text-sm text-green-400 font-mono">
          🟢 LIVE INGESTION ACTIVE
        </div>
      </header>

      {/* PANEL CONTROL FILTER (DEPENDENT DROPDOWN) */}
      <div className="bg-slate-800/80 border border-slate-700 p-5 rounded-2xl mb-8 flex flex-col md:flex-row items-center gap-5 shadow-xl">
        <div className="flex items-center space-x-3 text-blue-400 font-bold text-sm tracking-wide shrink-0">
          <Filter size={18} />
          <span>FILTER MONITORING AREA:</span>
        </div>
        
        {/* Dropdown 1: Kecamatan */}
        <div className="w-full md:w-64">
          <label className="block text-xs font-bold text-slate-400 uppercase mb-1.5">Kecamatan</label>
          <select
            value={selectedKecamatan}
            onChange={handleKecamatanChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 font-semibold"
          >
            <option value="">-- SEMUA KECAMATAN --</option>
            {listKecamatan.map((kec, i) => (
              <option key={i} value={kec}>{kec}</option>
            ))}
          </select>
        </div>

        {/* Dropdown 2: Kelurahan / Desa (Dependent) */}
        <div className="w-full md:w-64">
          <label className="block text-xs font-bold text-slate-400 uppercase mb-1.5">Kelurahan / Desa</label>
          <select
            value={selectedKelurahan}
            onChange={(e) => setSelectedKelurahan(e.target.value)}
            disabled={!selectedKecamatan}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <option value="">{selectedKecamatan ? "-- SEMUA KELURAHAN --" : "PILIH KECAMATAN DULU"}</option>
            {listKelurahan.map((kel, i) => (
              <option key={i} value={kel}>{kel}</option>
            ))}
          </select>
        </div>

        {/* Button Reset Filter */}
        {(selectedKecamatan || selectedKelurahan) && (
          <button
            onClick={() => { setSelectedKecamatan(''); setSelectedKelurahan(''); }}
            className="mt-5 md:mt-0 px-5 py-2.5 bg-slate-700 hover:bg-slate-600 rounded-xl text-sm font-bold transition-all text-slate-200"
          >
            Reset Filter
          </button>
        )}
      </div>

      {/* TIGA KARTU KPI UTAMA (Dihitung Reaktif Berdasarkan Filter) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <DashboardCard title="Beban Target Terfilter" value={globalStats.target} color="border-blue-500 bg-slate-800/50" />
        <DashboardCard title="Kuesioner Masuk (Submitted)" value={globalStats.selesai} color="border-green-500 bg-slate-800/50" />
        <DashboardCard title="Sisa Beban Lapangan (Open)" value={globalStats.sisa} color="border-amber-500 bg-slate-800/50" />
      </div>

      {/* NAVIGASI TAB KONTROL */}
      <div className="flex space-x-4 mb-6 bg-slate-800 p-1.5 rounded-xl w-fit border border-slate-700">
        <button onClick={() => setActiveTab('desa')} className={`flex items-center space-x-2 px-6 py-2.5 rounded-lg text-sm font-bold transition-all ${activeTab === 'desa' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}>
          <Layers size={16} /> <span>TAB 1: PROGRES PER DESA</span>
        </button>
        <button onClick={() => setActiveTab('petugas')} className={`flex items-center space-x-2 px-6 py-2.5 rounded-lg text-sm font-bold transition-all ${activeTab === 'petugas' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}>
          <Users size={16} /> <span>TAB 2: KINERJA PER PETUGAS</span>
        </button>
        <button onClick={() => setActiveTab('harian')} className={`flex items-center space-x-2 px-6 py-2.5 rounded-lg text-sm font-bold transition-all ${activeTab === 'harian' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : 'text-slate-400 hover:text-white'}`}>
          <TrendingUp size={16} /> <span>TAB 3: TREN PROGRES HARIAN</span>
        </button>
      </div>

      {/* VIEWPORT CONTROLLER CONTAINER (DI SINI KITA MENGGUNAKAN MODULARNYA!) */}
      <div className="bg-slate-800/60 backdrop-blur-xl border border-slate-700/60 rounded-2xl p-6 shadow-2xl">
        
        {/* Panggil komponen dan lemparkan datanya menggunakan Props */}
        {activeTab === 'desa' && <TabDesa dataDesa={filteredDataDesa} />}
        {activeTab === 'petugas' && <TabPetugas dataPetugas={filteredDataPetugas} dataTimeline={dataTimeline} />}
        {activeTab === 'harian' && <TabHarian chartData={chartDataHarian} />}

      </div>
    </div>
  );
}

export default App; 
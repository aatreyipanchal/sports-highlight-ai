"use client";

import { Upload, Video, Sparkles, Clock, Search } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [highlights, setHighlights] = useState<any[]>([]);
  const [fileId, setFileId] = useState<string | null>(null);
  const [filePath, setFilePath] = useState<string | null>(null);
  const [manualTime, setManualTime] = useState("");
  const [manualDescription, setManualDescription] = useState<string | null>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setIsUploading(true);

    const formData = new FormData();
    formData.append("file", selectedFile);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      const res = await fetch(`${apiUrl}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setFileId(data.file_id);
      setFilePath(data.file_path);
      
      // Auto-trigger highlights
      const hRes = await fetch(`${apiUrl}/highlights/${data.file_id}`);
      const hData = await hRes.json();
      setHighlights(hData.highlights);
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleManualRequest = async () => {
    if (!manualTime || !filePath) return;
    
    // Simple parser for HH:MM:SS or MM:SS
    const parts = manualTime.split(':').map(Number);
    let seconds = 0;
    if (parts.length === 3) seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
    else if (parts.length === 2) seconds = parts[0] * 60 + parts[1];
    else seconds = parts[0];

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      const res = await fetch(`${apiUrl}/describe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_path: filePath,
          start: Math.max(0, seconds - 2),
          end: seconds + 2
        }),
      });
      const data = await res.json();
      setManualDescription(data.description);
      // Add to highlights list if not there
      setHighlights(prev => [{
        id: `manual-${Date.now()}`,
        start: Math.max(0, seconds - 2),
        end: seconds + 2,
        description: `Manual Query Result: ${data.description}`,
        score: 1.0
      }, ...prev]);
    } catch (err) {
      console.error("Manual request failed", err);
    }
  };

  return (
    <main className="max-w-6xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="flex flex-col items-center text-center space-y-4 mb-16">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-blue-500/20 bg-blue-500/5 text-blue-400 text-sm font-medium"
        >
          <Sparkles className="w-4 h-4" />
          <span>Professional Sports Analysis</span>
        </motion.div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight">
          Sports Highlight <span className="gradient-text">AI</span>
        </h1>
        <p className="text-neutral-400 text-lg max-w-xl">
          Identify game-changing moments automatically. Powered by AI Temporal Segment Selection.
        </p>
      </div>

      {/* Upload Zone or Dashboard */}
      {!fileId ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative group block w-full rounded-2xl border-2 border-dashed border-neutral-800 p-12 text-center hover:border-blue-500/50 transition-colors cursor-pointer glass"
        >
          <input
            type="file"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            onChange={handleUpload}
            accept="video/*"
          />
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 rounded-2xl bg-neutral-900 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
              <Upload className="w-8 h-8 text-blue-500" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Drop your match recording</h3>
            <p className="text-neutral-500">Supports MP4, MOV, and AVI</p>
          </div>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Video Area */}
          <div className="lg:col-span-2 space-y-8">
             <div className="aspect-video rounded-3xl overflow-hidden bg-neutral-900 border border-neutral-800 shadow-2xl relative group">
                {isUploading ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center space-y-4 bg-neutral-900/80 backdrop-blur-sm z-10">
                    <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
                    <p className="text-blue-400 font-medium tracking-wide">Sports AI is mapping segments...</p>
                  </div>
                ) : null}
                
                {fileId ? (
                  <video 
                    controls 
                    className="w-full h-full object-cover"
                    src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/videos/${fileId}${file?.name.substring(file.name.lastIndexOf('.'))}`}
                  />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-neutral-600">
                    <Video className="w-12 h-12 mb-4 opacity-10 group-hover:opacity-20 transition-opacity" />
                    <span className="font-medium italic opacity-30">Waiting for recording upload...</span>
                  </div>
                )}
             </div>

             {/* Manual Request */}
             <div className="glass p-8 rounded-3xl space-y-4">
                <div className="flex items-center space-x-3 mb-2">
                  <Search className="w-5 h-5 text-blue-500" />
                  <h3 className="text-lg font-semibold">Custom Time Frame</h3>
                </div>
                <div className="flex gap-4">
                  <input 
                    type="text" 
                    value={manualTime}
                    onChange={(e) => setManualTime(e.target.value)}
                    placeholder="e.g. 05:20" 
                    className="flex-1 bg-neutral-900 border border-neutral-800 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-colors text-white" 
                  />
                  <button 
                    onClick={handleManualRequest}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-xl font-bold shadow-lg shadow-blue-500/20 transition-all active:scale-95"
                  >
                    Analyze
                  </button>
                </div>
                {manualDescription && (
                  <motion.p 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className={`font-medium p-4 rounded-xl border ${
                      manualDescription.includes("SCORE!") 
                        ? "bg-green-500/10 border-green-500/20 text-green-400" 
                        : "bg-blue-500/5 text-blue-400 border-blue-500/10"
                    }`}
                  >
                    AI Observation: {manualDescription}
                  </motion.p>
                )}
             </div>
          </div>

          {/* Highlights Sidebar */}
          <div className="space-y-6">
             <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold flex items-center gap-2">
                   <Clock className="w-5 h-5 text-blue-500" />
                   AI Highlights
                </h2>
                <span className="text-xs font-medium bg-neutral-800 px-2 py-1 rounded text-neutral-400 uppercase tracking-wider">{highlights.length} Detected</span>
             </div>
             
             <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 scrollbar-none">
                <AnimatePresence initial={false}>
                  {highlights.map((h, i) => (
                    <motion.div
                      key={h.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="group p-5 rounded-2xl glass hover:bg-white/5 transition-all cursor-pointer relative overflow-hidden"
                    >
                      <div className="absolute top-0 left-0 w-1 h-full bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                      <div className="flex justify-between items-start mb-2 text-sm">
                        <div className="flex flex-col">
                          <span className="font-mono text-blue-400">{typeof h.start === 'number' ? h.start.toFixed(1) : h.start}s - {typeof h.end === 'number' ? h.end.toFixed(1) : h.end}s</span>
                          {h.label === "POINT/SCORE!" && (
                            <span className="mt-1 text-[10px] font-bold bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded border border-green-500/30 w-fit uppercase tracking-tighter italic">
                              🏆 Score/Point Detected
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-neutral-500">Score: {Math.round((h.score || 0) * 100)}%</span>
                      </div>
                      <p className="text-sm font-medium leading-relaxed">{h.description}</p>
                    </motion.div>
                  ))}
                </AnimatePresence>
             </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="mt-24 pt-12 border-t border-neutral-900 text-center text-neutral-600 text-sm">
        &copy; 2026 Sports Highlight AI. All rights reserved. Built for champions.
      </footer>
    </main>
  );
}

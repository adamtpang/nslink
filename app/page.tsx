"use client";

import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera, Save, RotateCcw, Zap, CheckCircle, Smartphone } from 'lucide-react';
import { db } from '@/lib/firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';

export default function Scanner() {
  const webcamRef = useRef<Webcam>(null);
  const [imgSrc, setImgSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [scannedData, setScannedData] = useState<any>(null);
  const [status, setStatus] = useState<string>('');

  // Camera settings for mobile (rear camera)
  const videoConstraints = {
    facingMode: { exact: "environment" }
  };

  // 1. Capture Image
  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      setImgSrc(imageSrc);
      processImage(imageSrc);
    }
  }, [webcamRef]);

  // 2. Send to Gemini Flash (Server-Side)
  const processImage = async (base64Image: string) => {
    setLoading(true);
    setStatus('Analyzing Label...');

    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: base64Image }),
      });

      const data = await response.json();
      setScannedData(data);
      setStatus('Review Data');
    } catch (error) {
      console.error(error);
      setStatus('Error scanning. Try again.');
    } finally {
      setLoading(false);
    }
  };

  // 3. Save to Firestore "Queue"
  const handleSave = async () => {
    if (!scannedData) return;
    setStatus('Saving to Queue...');

    try {
      await addDoc(collection(db, "router_queue"), {
        serial_number: scannedData.serial_number,
        default_ssid: scannedData.default_ssid,
        default_pass: scannedData.default_pass,
        sim_id: scannedData.sim_id || "", // Manual entry might be needed for SIM
        target_ssid: `NS-Room-Waitlist`, // Default target, changeable later
        status: "PENDING", // Ready for Python script
        created_at: serverTimestamp()
      });

      // Reset for next router
      setImgSrc(null);
      setScannedData(null);
      setStatus('Saved! Ready for next.');
      setTimeout(() => setStatus(''), 2000);
    } catch (e) {
      console.error(e);
      setStatus('Error saving to DB');
    }
  };

  const handleRetake = () => {
    setImgSrc(null);
    setScannedData(null);
    setStatus('');
  };

  return (
    <div className="min-h-screen bg-neutral-900 text-green-500 font-mono p-4 flex flex-col items-center">
      <div className="w-full max-w-md flex justify-between items-center mb-6 border-b border-green-800 pb-2">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Zap className="w-5 h-5" /> NS_INGEST
        </h1>
        <span className="text-xs text-green-700 animate-pulse">SYSTEM_ONLINE</span>
      </div>

      <div className="w-full max-w-md bg-black border border-green-800 rounded-lg overflow-hidden relative min-h-[400px] flex flex-col justify-center">
        {/* Camera View */}
        {!imgSrc && (
          <>
            <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              videoConstraints={videoConstraints}
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-4 left-0 right-0 flex justify-center">
              <button
                onClick={capture}
                className="bg-green-600 hover:bg-green-500 text-black rounded-full p-4 shadow-[0_0_20px_rgba(34,197,94,0.5)] transition-all active:scale-95"
              >
                <Camera size={32} />
              </button>
            </div>
            {/* Overlay Grid */}
            <div className="absolute inset-0 pointer-events-none border-2 border-green-500/30 m-8 rounded-lg">
              <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-green-500"></div>
              <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-green-500"></div>
              <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-green-500"></div>
              <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-green-500"></div>
            </div>
          </>
        )}

        {/* Review View */}
        {imgSrc && (
          <div className="p-4 space-y-4">
            <img src={imgSrc} alt="Scanned" className="w-full h-48 object-cover rounded border border-green-800 opacity-50" />

            {loading ? (
              <div className="text-center py-8 animate-pulse">
                <p>EXTRACTING_DATA...</p>
                <p className="text-xs text-green-700">Gemini Flash Vision Active</p>
              </div>
            ) : (
              <div className="space-y-3">
                {/* Editable Fields */}
                <div className="space-y-1">
                  <label className="text-xs text-green-700">SERIAL_NUMBER</label>
                  <input
                    value={scannedData?.serial_number || ''}
                    onChange={(e) => setScannedData({...scannedData, serial_number: e.target.value})}
                    className="w-full bg-neutral-900 border border-green-800 p-2 rounded text-white focus:outline-none focus:border-green-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-green-700">DEFAULT_SSID</label>
                  <input
                    value={scannedData?.default_ssid || ''}
                    onChange={(e) => setScannedData({...scannedData, default_ssid: e.target.value})}
                    className="w-full bg-neutral-900 border border-green-800 p-2 rounded text-white focus:outline-none focus:border-green-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-green-700">DEFAULT_PASS</label>
                  <input
                    value={scannedData?.default_pass || ''}
                    onChange={(e) => setScannedData({...scannedData, default_pass: e.target.value})}
                    className="w-full bg-neutral-900 border border-green-800 p-2 rounded text-white focus:outline-none focus:border-green-500"
                  />
                </div>
                {/* Optional SIM Field if you scan SIM card separately or same time */}
                <div className="space-y-1">
                  <label className="text-xs text-green-700">SIM_ICCID (Optional)</label>
                  <input
                    value={scannedData?.sim_id || ''}
                    onChange={(e) => setScannedData({...scannedData, sim_id: e.target.value})}
                    placeholder="Scan SIM next or type..."
                    className="w-full bg-neutral-900 border border-green-800 p-2 rounded text-white focus:outline-none focus:border-green-500"
                  />
                </div>

                <div className="flex gap-2 mt-4">
                  <button
                    onClick={handleRetake}
                    className="flex-1 bg-red-900/30 text-red-500 border border-red-900 p-3 rounded flex justify-center items-center gap-2 hover:bg-red-900/50"
                  >
                    <RotateCcw size={18} /> RETAKE
                  </button>
                  <button
                    onClick={handleSave}
                    className="flex-1 bg-green-600 text-black p-3 rounded flex justify-center items-center gap-2 font-bold hover:bg-green-500"
                  >
                    <Save size={18} /> SAVE
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {status && (
        <div className="mt-4 flex items-center gap-2 text-sm text-green-400 bg-green-900/20 px-4 py-2 rounded-full border border-green-900/50">
           {status.includes("Saved") ? <CheckCircle size={16} /> : <Smartphone size={16} />}
           {status}
        </div>
      )}
    </div>
  );
}
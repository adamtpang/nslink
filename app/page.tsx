"use client";

import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera, Save, RotateCcw, Zap, CheckCircle, Smartphone, ScanLine } from 'lucide-react';
import { db } from '@/lib/firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MotionWrapper, MotionItem } from "@/components/motion-wrapper";

export default function Scanner() {
  const webcamRef = useRef<Webcam>(null);
  const [imgSrc, setImgSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [scannedData, setScannedData] = useState<any>(null);
  const [status, setStatus] = useState<string>('');

  const videoConstraints = {
    facingMode: { exact: "environment" }
  };

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      setImgSrc(imageSrc);
      processImage(imageSrc);
    }
  }, [webcamRef]);

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

  const handleSave = async () => {
    if (!scannedData) return;
    setStatus('Saving to Queue...');

    try {
      await addDoc(collection(db, "router_queue"), {
        serial_number: scannedData.serial_number,
        default_ssid: scannedData.default_ssid,
        default_pass: scannedData.default_pass,
        sim_id: scannedData.sim_id || "",
        target_ssid: scannedData.target_ssid || "NS-Room-Waitlist",
        status: "PENDING",
        created_at: serverTimestamp()
      });

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
    <div className="min-h-screen bg-background text-foreground font-sans p-4 flex flex-col items-center justify-center">
      <MotionWrapper animation="fadeIn" className="w-full max-w-md space-y-6">

        {/* Header */}
        <div className="flex justify-between items-center border-b border-border pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-primary/10 rounded-full">
              <Zap className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">NS_LINK</h1>
              <p className="text-xs text-muted-foreground">Router Ingestion System</p>
            </div>
          </div>
          <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-1 rounded animate-pulse">
            ONLINE
          </span>
        </div>

        {/* Main Card */}
        <Card className="overflow-hidden border-primary/20 shadow-lg shadow-primary/5">
          <CardContent className="p-0 relative min-h-[400px] flex flex-col justify-center bg-black/50">

            {/* Camera View */}
            {!imgSrc && (
              <div className="relative h-full">
                <Webcam
                  audio={false}
                  ref={webcamRef}
                  screenshotFormat="image/jpeg"
                  videoConstraints={videoConstraints}
                  className="w-full h-[400px] object-cover"
                />

                {/* Overlay UI */}
                <div className="absolute inset-0 flex flex-col justify-between p-6 pointer-events-none">
                  <div className="w-full h-full border-2 border-primary/30 rounded-lg relative">
                    <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-primary rounded-tl-lg" />
                    <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-primary rounded-tr-lg" />
                    <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-primary rounded-bl-lg" />
                    <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-primary rounded-br-lg" />

                    <div className="absolute inset-0 flex items-center justify-center">
                      <ScanLine className="w-64 h-64 text-primary/20 animate-pulse" />
                    </div>
                  </div>
                </div>

                <div className="absolute bottom-6 left-0 right-0 flex justify-center pointer-events-auto">
                  <Button
                    onClick={capture}
                    size="icon"
                    className="h-16 w-16 rounded-full shadow-[0_0_30px_rgba(34,197,94,0.4)] border-4 border-background hover:scale-105 transition-transform"
                  >
                    <Camera className="w-8 h-8" />
                  </Button>
                </div>
              </div>
            )}

            {/* Review View */}
            {imgSrc && (
              <MotionWrapper animation="scaleIn" className="p-6 space-y-6 bg-card">
                <div className="relative rounded-lg overflow-hidden border border-border">
                  <img src={imgSrc} alt="Scanned" className="w-full h-48 object-cover opacity-75" />
                  <div className="absolute inset-0 bg-gradient-to-t from-background/90 to-transparent" />
                  <div className="absolute bottom-2 left-2">
                    <span className="text-xs bg-black/50 text-white px-2 py-1 rounded backdrop-blur-sm">
                      CAPTURED
                    </span>
                  </div>
                </div>

                {loading ? (
                  <div className="text-center py-8 space-y-2">
                    <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                    <p className="text-sm font-medium animate-pulse">Extracting Data...</p>
                    <p className="text-xs text-muted-foreground">Gemini Flash Vision Active</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid gap-4">
                      <div className="space-y-2">
                        <Label>Serial Number</Label>
                        <Input
                          value={scannedData?.serial_number || ''}
                          onChange={(e) => setScannedData({ ...scannedData, serial_number: e.target.value })}
                          className="font-mono"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Default SSID</Label>
                          <Input
                            value={scannedData?.default_ssid || ''}
                            onChange={(e) => setScannedData({ ...scannedData, default_ssid: e.target.value })}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Default Pass</Label>
                          <Input
                            value={scannedData?.default_pass || ''}
                            onChange={(e) => setScannedData({ ...scannedData, default_pass: e.target.value })}
                            type="text"
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-primary">Target SSID (New Name)</Label>
                        <Input
                          value={scannedData?.target_ssid || ''}
                          onChange={(e) => setScannedData({ ...scannedData, target_ssid: e.target.value })}
                          placeholder="e.g. NS Room 8019"
                          className="border-primary/50 bg-primary/5 font-bold"
                        />
                      </div>
                    </div>

                    <div className="flex gap-3 pt-2">
                      <Button variant="outline" onClick={handleRetake} className="flex-1 gap-2">
                        <RotateCcw className="w-4 h-4" /> Retake
                      </Button>
                      <Button onClick={handleSave} className="flex-1 gap-2 font-bold">
                        <Save className="w-4 h-4" /> Save to Queue
                      </Button>
                    </div>
                  </div>
                )}
              </MotionWrapper>
            )}

          </CardContent>
        </Card>

        {/* Status Toast */}
        {status && (
          <MotionWrapper animation="slideInLeft" className="flex justify-center">
            <div className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border shadow-lg backdrop-blur-sm",
              status.includes("Saved")
                ? "bg-green-500/10 text-green-500 border-green-500/20"
                : "bg-primary/10 text-primary border-primary/20"
            )}>
              {status.includes("Saved") ? <CheckCircle size={16} /> : <Smartphone size={16} />}
              {status}
            </div>
          </MotionWrapper>
        )}

      </MotionWrapper>
    </div>
  );
}
"use client";

import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera, Save, RotateCcw, Zap, CheckCircle, Smartphone, ScanLine, Upload, Trash2, Play, Plus, FileDown, Table, X } from 'lucide-react';
import { db } from '@/lib/firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MotionWrapper, MotionItem } from "@/components/motion-wrapper";

interface ScannedImage {
  id: string;
  src: string;
  status: 'idle' | 'analyzing' | 'done' | 'error';
  data?: {
    serial_number: string;
    default_ssid: string;
    default_pass: string;
    target_ssid?: string;
  };
}

export default function Scanner() {
  const webcamRef = useRef<Webcam>(null);
  const [images, setImages] = useState<ScannedImage[]>([]);
  const [activeTab, setActiveTab] = useState("camera");
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const videoConstraints = {
    facingMode: { exact: "environment" }
  };

  // 1. Capture from Camera
  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      const newImage: ScannedImage = {
        id: Date.now().toString(),
        src: imageSrc,
        status: 'idle'
      };
      setImages(prev => [...prev, newImage]);
    }
  }, [webcamRef]);

  // 2. Upload from File
  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      files.forEach(file => {
        const reader = new FileReader();
        reader.onloadend = () => {
          setImages(prev => [...prev, {
            id: Math.random().toString(36).substr(2, 9),
            src: reader.result as string,
            status: 'idle'
          }]);
        };
        reader.readAsDataURL(file);
      });
    }
  };

  // 3. Process Single Image (Helper)
  const analyzeImage = async (img: ScannedImage) => {
    let attempts = 0;
    const maxAttempts = 3;

    while (attempts < maxAttempts) {
      try {
        attempts++;
        const response = await fetch('/api/scan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: img.src }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Basic validation: Check if we got at least a serial number or an empty object that isn't an error
        if (data.error) {
          throw new Error(data.error);
        }

        return { ...img, status: 'done' as const, data };
      } catch (error) {
        console.error(`Attempt ${attempts} failed:`, error);
        if (attempts === maxAttempts) {
          return { ...img, status: 'error' as const };
        }
        // Wait 1s before retrying
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    return { ...img, status: 'error' as const };
  };

  // 4. Batch Analyze
  const handleAnalyzeAll = async () => {
    setIsBatchProcessing(true);
    const newImages = [...images];

    for (let i = 0; i < newImages.length; i++) {
      if (newImages[i].status === 'idle') {
        newImages[i].status = 'analyzing';
        setImages([...newImages]); // Update UI

        const result = await analyzeImage(newImages[i]);
        newImages[i] = result;
        setImages([...newImages]); // Update UI
      }
    }
    setIsBatchProcessing(false);
  };

  // 5. Generate CSV Content
  const generateCSVContent = () => {
    const readyImages = images.filter(img => img.status === 'done' && img.data);
    if (readyImages.length === 0) return null;

    const headers = ["serial_number", "default_ssid", "default_pass", "target_ssid"];
    const csvRows = readyImages.map(img => {
      const d = img.data!;
      return [d.serial_number, d.default_ssid, d.default_pass, d.target_ssid || ""].join(",");
    });

    return [headers.join(","), ...csvRows].join("\n");
  };

  // 6. Download CSV
  const handleDownloadCSV = () => {
    const csvContent = generateCSVContent();
    if (!csvContent) return;

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'router_queue.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const removeImage = (id: string) => {
    setImages(prev => prev.filter(img => img.id !== id));
  };

  const updateImageData = (id: string, field: string, value: string) => {
    setImages(prev => prev.map(img => {
      if (img.id === id && img.data) {
        return { ...img, data: { ...img.data, [field]: value } };
      }
      return img;
    }));
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans p-4 flex flex-col items-center">
      <MotionWrapper animation="fadeIn" className="w-full max-w-4xl space-y-6">

        {/* Header */}
        <div className="flex justify-between items-center border-b border-border pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-primary/10 rounded-full">
              <Zap className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">NS_LINK</h1>
              <p className="text-xs text-muted-foreground">Batch Router Ingestion</p>
            </div>
          </div>
          <div className="flex gap-2">
            <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-1 rounded">
              QUEUE: {images.length}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Left Column: Input */}
          <Card className="border-primary/20 shadow-lg shadow-primary/5 h-fit">
            <Tabs defaultValue="camera" className="w-full" onValueChange={setActiveTab}>
              <CardHeader className="pb-2">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="camera">Camera</TabsTrigger>
                  <TabsTrigger value="upload">Upload</TabsTrigger>
                </TabsList>
              </CardHeader>
              <CardContent className="p-4">
                <TabsContent value="camera" className="mt-0">
                  <div className="relative rounded-lg overflow-hidden bg-black aspect-video mb-4">
                    <Webcam
                      audio={false}
                      ref={webcamRef}
                      screenshotFormat="image/jpeg"
                      videoConstraints={videoConstraints}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <ScanLine className="w-32 h-32 text-primary/20 animate-pulse" />
                    </div>
                  </div>
                  <Button onClick={capture} className="w-full gap-2 font-bold" size="lg">
                    <Camera className="w-5 h-5" /> Capture to Queue
                  </Button>
                </TabsContent>

                <TabsContent value="upload" className="mt-0">
                  <div className="border-2 border-dashed border-border rounded-lg p-8 flex flex-col items-center justify-center gap-4 hover:bg-accent/50 transition-colors cursor-pointer relative">
                    <Upload className="w-12 h-12 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground text-center">
                      Drag & drop or click to upload multiple files
                    </p>
                    <Input
                      type="file"
                      multiple
                      accept="image/*"
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      onChange={handleUpload}
                    />
                  </div>
                </TabsContent>
              </CardContent>
            </Tabs>
          </Card>

          {/* Right Column: Queue */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Processing Queue</h2>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleAnalyzeAll}
                  disabled={isBatchProcessing || images.length === 0}
                >
                  <Play className="w-4 h-4 mr-2" /> Analyze All
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowPreview(true)}
                  disabled={images.filter(i => i.status === 'done').length === 0}
                >
                  <Table className="w-4 h-4 mr-2" /> Preview CSV
                </Button>

                <Button
                  size="sm"
                  onClick={handleDownloadCSV}
                  disabled={images.filter(i => i.status === 'done').length === 0}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  <FileDown className="w-4 h-4 mr-2" /> Download CSV
                </Button>
              </div>
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
              {images.length === 0 && (
                <div className="text-center py-12 text-muted-foreground border border-dashed rounded-lg">
                  No images in queue
                </div>
              )}

              {images.map((img, idx) => (
                <MotionWrapper key={img.id} animation="slideInRight" delay={idx * 0.1}>
                  <Card className="overflow-hidden">
                    <div className="flex gap-4 p-3">
                      <div className="w-24 h-24 flex-shrink-0 bg-black rounded overflow-hidden relative">
                        <img src={img.src} className="w-full h-full object-cover" />
                        {img.status === 'analyzing' && (
                          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                          </div>
                        )}
                        {img.status === 'done' && (
                          <div className="absolute top-1 right-1 bg-green-500 rounded-full p-0.5">
                            <CheckCircle className="w-3 h-3 text-white" />
                          </div>
                        )}
                      </div>

                      <div className="flex-1 min-w-0 space-y-2">
                        {img.status === 'done' && img.data ? (
                          <>
                            <div className="grid grid-cols-2 gap-2">
                              <Input
                                value={img.data.serial_number}
                                onChange={(e) => updateImageData(img.id, 'serial_number', e.target.value)}
                                className="h-7 text-xs font-mono"
                                placeholder="S/N"
                              />
                              <Input
                                value={img.data.target_ssid || ''}
                                onChange={(e) => updateImageData(img.id, 'target_ssid', e.target.value)}
                                className="h-7 text-xs font-bold border-primary/50"
                                placeholder="Target SSID"
                              />
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              <Input
                                value={img.data.default_ssid}
                                onChange={(e) => updateImageData(img.id, 'default_ssid', e.target.value)}
                                className="h-7 text-xs"
                                placeholder="SSID"
                              />
                              <Input
                                value={img.data.default_pass}
                                onChange={(e) => updateImageData(img.id, 'default_pass', e.target.value)}
                                className="h-7 text-xs"
                                placeholder="Pass"
                              />
                            </div>
                          </>
                        ) : (
                          <div className="h-full flex items-center text-sm text-muted-foreground">
                            {img.status === 'idle' ? 'Ready to analyze' :
                              img.status === 'analyzing' ? 'Extracting data...' : 'Error extracting data'}
                          </div>
                        )}
                      </div>

                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                        onClick={() => removeImage(img.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </Card>
                </MotionWrapper>
              ))}
            </div>
          </div>
        </div>

      </MotionWrapper>

      {/* PREVIEW MODAL */}
      {showPreview && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <MotionWrapper animation="scaleIn" className="w-full max-w-3xl bg-background border border-border rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
            <div className="flex justify-between items-center p-4 border-b border-border bg-muted/30">
              <div className="flex items-center gap-2">
                <Table className="w-5 h-5 text-primary" />
                <h3 className="font-bold">CSV Preview</h3>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setShowPreview(false)}>
                <X className="w-5 h-5" />
              </Button>
            </div>

            <div className="p-0 overflow-auto flex-1 bg-card">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-muted/50 sticky top-0">
                  <tr>
                    <th className="px-4 py-3">Serial Number</th>
                    <th className="px-4 py-3">Default SSID</th>
                    <th className="px-4 py-3">Default Pass</th>
                    <th className="px-4 py-3">Target SSID</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {images.filter(i => i.status === 'done' && i.data).map((img) => (
                    <tr key={img.id} className="hover:bg-muted/20">
                      <td className="px-4 py-3 font-mono">{img.data?.serial_number}</td>
                      <td className="px-4 py-3">{img.data?.default_ssid}</td>
                      <td className="px-4 py-3 font-mono">{img.data?.default_pass}</td>
                      <td className="px-4 py-3 font-bold text-primary">{img.data?.target_ssid || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-4 border-t border-border bg-muted/30 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowPreview(false)}>Close</Button>
              <Button onClick={() => { handleDownloadCSV(); setShowPreview(false); }} className="bg-green-600 hover:bg-green-700 text-white">
                <FileDown className="w-4 h-4 mr-2" /> Download CSV
              </Button>
            </div>
          </MotionWrapper>
        </div>
      )}
    </div>
  );
}
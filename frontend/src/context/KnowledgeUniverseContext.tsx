import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export interface UniverseNode {
  id: number;
  name: string;
  cluster: 'HR' | 'Finance' | 'Security' | 'Engineering' | 'Legal' | 'Compliance' | 'Marketing';
  x: number; // 3D coordinates (-100 to 100)
  y: number;
  z: number;
  vx: number; // velocity for drifting
  vy: number;
  vz: number;
  size: number;
  opacity: number;
  glowing: boolean;
  score?: number; // similarity score (0 to 1)
  status: 'active' | 'dimmed' | 'hidden';
}

export interface UniverseEdge {
  from: number;
  to: number;
  active: boolean;
}

export interface SatelliteParticle {
  id: string;
  name: string;
  progress: number; // 0 to 1
  startX: number;
  startY: number;
  targetNodeId: number;
  stage: 'upload' | 'parse' | 'chunk' | 'embed' | 'vector' | 'index';
}

export interface QueryOrb {
  x: number;
  y: number;
  progress: number; // 0 to 1 (shooting)
  active: boolean;
}

export interface PulseWave {
  x: number;
  y: number;
  radius: number;
  maxRadius: number;
  active: boolean;
}

interface KnowledgeUniverseContextType {
  nodes: UniverseNode[];
  edges: UniverseEdge[];
  searchStep: number;
  activeQuery: string;
  answerText: string;
  similarityResults: any[];
  activeCitations: number[];
  satellites: SatelliteParticle[];
  queryOrb: QueryOrb;
  pulseWave: PulseWave;
  triggerSearchSequence: (query: string, results: any[], answer: string) => Promise<void>;
  triggerIngestSequence: (docName: string, targetCluster?: UniverseNode['cluster']) => void;
  setHoveredCitation: (docId: number | null) => void;
  resetSearch: () => void;
  loadDocumentsIntoUniverse: () => Promise<void>;
}

const KnowledgeUniverseContext = createContext<KnowledgeUniverseContextType | undefined>(undefined);

const DEFAULT_CLUSTERS: UniverseNode['cluster'][] = [
  'HR', 'Finance', 'Security', 'Engineering', 'Legal', 'Compliance', 'Marketing'
];

const getClusterColor = (cluster: UniverseNode['cluster']) => {
  switch (cluster) {
    case 'Security': return '#10B981'; // bright emerald
    case 'Engineering': return '#34D399'; // cyber green
    case 'Legal': return '#059669'; // medium green
    case 'Compliance': return '#047857'; // forest green
    case 'HR': return '#6B7280'; // soft gray
    case 'Finance': return '#9CA3AF'; // charcoal gray
    default: return '#10B981';
  }
};

export const KnowledgeUniverseProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [nodes, setNodes] = useState<UniverseNode[]>([]);
  const [edges, setEdges] = useState<UniverseEdge[]>([]);
  const [searchStep, setSearchStep] = useState<number>(0);
  const [activeQuery, setActiveQuery] = useState<string>('');
  const [answerText, setAnswerText] = useState<string>('');
  const [similarityResults, setSimilarityResults] = useState<any[]>([]);
  const [activeCitations, setActiveCitations] = useState<number[]>([]);
  const [satellites, setSatellites] = useState<SatelliteParticle[]>([]);
  const [queryOrb, setQueryOrb] = useState<QueryOrb>({ x: 0, y: 0, progress: 0, active: false });
  const [pulseWave, setPulseWave] = useState<PulseWave>({ x: 0, y: 0, radius: 0, maxRadius: 150, active: false });

  // Helper to generate mock baseline nodes if documents are empty
  const generateMockNodes = (): UniverseNode[] => {
    const mockList: UniverseNode[] = [];
    const nodeCount = 50;

    for (let i = 1; i <= nodeCount; i++) {
      const cluster = DEFAULT_CLUSTERS[i % DEFAULT_CLUSTERS.length];
      // Generate cluster centers in 3D
      const angle = (DEFAULT_CLUSTERS.indexOf(cluster) / DEFAULT_CLUSTERS.length) * Math.PI * 2;
      const clusterRadius = 45;
      const centerX = Math.cos(angle) * clusterRadius;
      const centerY = Math.sin(angle) * clusterRadius;
      const centerZ = (i % 3 - 1) * 20;

      // Add dispersion
      const disp = 15;
      const x = centerX + (Math.random() * disp - disp / 2);
      const y = centerY + (Math.random() * disp - disp / 2);
      const z = centerZ + (Math.random() * disp - disp / 2);

      mockList.push({
        id: -i, // negative IDs for mock nodes
        name: `${cluster}_Protocol_v${i % 3 + 1}.bin`,
        cluster,
        x,
        y,
        z,
        vx: (Math.random() * 0.04 - 0.02),
        vy: (Math.random() * 0.04 - 0.02),
        vz: (Math.random() * 0.04 - 0.02),
        size: Math.random() * 2 + 1.5,
        opacity: Math.random() * 0.4 + 0.3,
        glowing: false,
        status: 'active'
      });
    }
    return mockList;
  };

  const loadDocumentsIntoUniverse = useCallback(async () => {
    try {
      const response = await api.get('/documents');
      const docs = response.data;
      
      const baselineMock = generateMockNodes();
      
      if (docs && docs.length > 0) {
        const docNodes = docs.map((doc: any, index: number) => {
          // Determine cluster based on extension or filename
          let cluster: UniverseNode['cluster'] = 'Engineering';
          const nameLower = doc.original_filename.toLowerCase();
          
          if (nameLower.includes('hr') || nameLower.includes('employee') || nameLower.includes('handbook')) {
            cluster = 'HR';
          } else if (nameLower.includes('finance') || nameLower.includes('tax') || nameLower.includes('invoice') || nameLower.includes('budget')) {
            cluster = 'Finance';
          } else if (nameLower.includes('security') || nameLower.includes('policy') || nameLower.includes('password') || nameLower.includes('iam')) {
            cluster = 'Security';
          } else if (nameLower.includes('legal') || nameLower.includes('contract') || nameLower.includes('nda')) {
            cluster = 'Legal';
          } else if (nameLower.includes('compliance') || nameLower.includes('audit') || nameLower.includes('regulation')) {
            cluster = 'Compliance';
          } else if (nameLower.includes('marketing') || nameLower.includes('social') || nameLower.includes('pr')) {
            cluster = 'Marketing';
          }
          
          const angle = (DEFAULT_CLUSTERS.indexOf(cluster) / DEFAULT_CLUSTERS.length) * Math.PI * 2;
          const clusterRadius = 45;
          const centerX = Math.cos(angle) * clusterRadius;
          const centerY = Math.sin(angle) * clusterRadius;
          const centerZ = 0;

          return {
            id: doc.id,
            name: doc.original_filename,
            cluster,
            x: centerX + (Math.random() * 10 - 5),
            y: centerY + (Math.random() * 10 - 5),
            z: centerZ + (Math.random() * 10 - 5),
            vx: (Math.random() * 0.03 - 0.015),
            vy: (Math.random() * 0.03 - 0.015),
            vz: (Math.random() * 0.03 - 0.015),
            size: 3.5,
            opacity: 0.8,
            glowing: false,
            status: 'active' as const
          };
        });

        // Merge user documents with baseline starfield
        setNodes([...docNodes, ...baselineMock]);
      } else {
        setNodes(baselineMock);
      }
    } catch (err) {
      console.error('Failed to load universe documents', err);
      setNodes(generateMockNodes());
    }
  }, []);

  // Update edges dynamically based on similarities/clusters
  useEffect(() => {
    if (nodes.length === 0) return;
    
    const newEdges: UniverseEdge[] = [];
    // Link nodes in the same cluster with 15% probability to form groups
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        if (nodes[i].cluster === nodes[j].cluster && Math.random() < 0.12) {
          newEdges.push({
            from: nodes[i].id,
            to: nodes[j].id,
            active: false
          });
        }
      }
    }
    setEdges(newEdges);
  }, [nodes]);

  useEffect(() => {
    loadDocumentsIntoUniverse();
  }, [loadDocumentsIntoUniverse]);

  // Handle slow physics simulation of drifting particles
  useEffect(() => {
    const interval = setInterval(() => {
      setNodes((prevNodes) =>
        prevNodes.map((n) => {
          // If in search step 5 or later, drift towards targeted locations
          if (searchStep >= 5) {
            return n; // handled separately in animation rendering
          }

          // Normal space drift
          let nx = n.x + n.vx;
          let ny = n.y + n.vy;
          let nz = n.z + n.vz;

          // Boundary bounce or wrap
          if (Math.abs(nx) > 85) n.vx *= -1;
          if (Math.abs(ny) > 85) n.vy *= -1;
          if (Math.abs(nz) > 80) n.vz *= -1;

          return {
            ...n,
            x: nx,
            y: ny,
            z: nz
          };
        })
      );
    }, 33); // 30 FPS physics update loop

    return () => clearInterval(interval);
  }, [searchStep]);

  // 9-Step Cinematic Search sequence transition orchestrator
  const triggerSearchSequence = async (query: string, results: any[], answer: string) => {
    setActiveQuery(query);
    setSimilarityResults(results);
    setAnswerText(answer);

    // Step 1: Input text fades into energy orb
    setSearchStep(1);
    await new Promise(r => setTimeout(r, 600));

    // Step 2: Orb forming
    setSearchStep(2);
    setQueryOrb({ x: window.innerWidth / 2, y: window.innerHeight - 120, progress: 0, active: true });
    await new Promise(r => setTimeout(r, 800));

    // Step 3: Orb shoots to center of universe
    setSearchStep(3);
    let shootProgress = 0;
    const shootInterval = setInterval(() => {
      shootProgress += 0.05;
      if (shootProgress >= 1) {
        clearInterval(shootInterval);
      } else {
        setQueryOrb(prev => ({
          ...prev,
          progress: shootProgress,
          x: (window.innerWidth / 2) * (1 - shootProgress) + (window.innerWidth / 2) * shootProgress,
          y: (window.innerHeight - 120) * (1 - shootProgress) + (window.innerHeight / 2) * shootProgress
        }));
      }
    }, 16);
    await new Promise(r => setTimeout(r, 400));

    // Step 4: Pulse wave expands
    setSearchStep(4);
    setQueryOrb(prev => ({ ...prev, active: false }));
    setPulseWave({ x: window.innerWidth / 2, y: window.innerHeight / 2, radius: 0, maxRadius: 280, active: true });
    
    let pulseRadius = 0;
    const pulseInterval = setInterval(() => {
      pulseRadius += 10;
      if (pulseRadius >= 280) {
        clearInterval(pulseInterval);
        setPulseWave(prev => ({ ...prev, active: false }));
      } else {
        setPulseWave(prev => ({ ...prev, radius: pulseRadius }));
      }
    }, 16);
    await new Promise(r => setTimeout(r, 600));

    // Step 5: Filter documents, highlight relevant nodes, dim others
    setSearchStep(5);
    const matchedDocIds = results.map(r => r.document_id);
    
    setNodes(prev =>
      prev.map(node => {
        const isMatched = matchedDocIds.includes(node.id);
        return {
          ...node,
          glowing: isMatched,
          status: isMatched ? 'active' : 'dimmed',
          opacity: isMatched ? 1.0 : 0.08,
          // Move matched nodes closer to center visually
          x: isMatched ? node.x * 0.5 : node.x,
          y: isMatched ? node.y * 0.5 : node.y
        };
      })
    );
    await new Promise(r => setTimeout(r, 1000));

    // Step 6: Similarity scoring cards appear
    setSearchStep(6);
    await new Promise(r => setTimeout(r, 1200));

    // Step 7: Chunk explosion (Clicking/confirming automatically explodes or moves on)
    setSearchStep(7);
    await new Promise(r => setTimeout(r, 1200));

    // Step 8: Chunk assembly
    setSearchStep(8);
    await new Promise(r => setTimeout(r, 1000));

    // Step 9: Final grounded answer revealed
    setSearchStep(9);
  };

  const triggerIngestSequence = (docName: string, targetCluster: UniverseNode['cluster'] = 'Engineering') => {
    // Generate a temporary satellite particle
    const satId = `sat_${Date.now()}`;
    const newSat: SatelliteParticle = {
      id: satId,
      name: docName,
      progress: 0,
      startX: 80, // bottom-right panel position
      startY: window.innerHeight - 80,
      targetNodeId: 0, // targeted to cluster center coordinates
      stage: 'upload'
    };

    setSatellites(prev => [...prev, newSat]);

    // Animate satellite path
    let satProgress = 0;
    const satInterval = setInterval(() => {
      satProgress += 0.015;
      if (satProgress >= 1) {
        clearInterval(satInterval);
        setSatellites(prev => prev.filter(s => s.id !== satId));
        // Add new node to universe upon completing ingestion sequence
        loadDocumentsIntoUniverse();
      } else {
        setSatellites(prev =>
          prev.map(s => {
            if (s.id !== satId) return s;
            
            // Map stages
            let stage: SatelliteParticle['stage'] = 'upload';
            if (satProgress > 0.8) stage = 'index';
            else if (satProgress > 0.6) stage = 'vector';
            else if (satProgress > 0.4) stage = 'embed';
            else if (satProgress > 0.2) stage = 'chunk';
            
            return {
              ...s,
              progress: satProgress,
              stage
            };
          })
        );
      }
    }, 24);
  };

  const setHoveredCitation = (docId: number | null) => {
    if (docId === null) {
      setActiveCitations([]);
      // Restore node status
      setNodes(prev => prev.map(n => ({ ...n, glowing: false })));
    } else {
      setActiveCitations([docId]);
      setNodes(prev =>
        prev.map(n => {
          if (n.id === docId) {
            return { ...n, glowing: true, opacity: 1.0 };
          }
          return n;
        })
      );
    }
  };

  const resetSearch = () => {
    setSearchStep(0);
    setActiveQuery('');
    setAnswerText('');
    setSimilarityResults([]);
    setNodes(prev =>
      prev.map(n => ({
        ...n,
        glowing: false,
        opacity: n.id < 0 ? 0.35 : 0.8,
        status: 'active'
      }))
    );
  };

  return (
    <KnowledgeUniverseContext.Provider
      value={{
        nodes,
        edges,
        searchStep,
        activeQuery,
        answerText,
        similarityResults,
        activeCitations,
        satellites,
        queryOrb,
        pulseWave,
        triggerSearchSequence,
        triggerIngestSequence,
        setHoveredCitation,
        resetSearch,
        loadDocumentsIntoUniverse
      }}
    >
      {children}
    </KnowledgeUniverseContext.Provider>
  );
};

export const useKnowledgeUniverse = () => {
  const context = useContext(KnowledgeUniverseContext);
  if (context === undefined) {
    throw new Error('useKnowledgeUniverse must be used within a KnowledgeUniverseProvider');
  }
  return context;
};

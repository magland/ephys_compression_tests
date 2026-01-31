export type SupportedTypedArray =
  | Uint8Array
  | Uint16Array
  | Uint32Array
  | Int16Array
  | Int32Array
  | Float32Array;

interface ChunkCache {
  [key: number]: SupportedTypedArray;
}

type DType = "uint8" | "uint16" | "uint32" | "int16" | "int32" | "float32";

const TypedArrayConstructors = {
  uint8: Uint8Array,
  uint16: Uint16Array,
  uint32: Uint32Array,
  int16: Int16Array,
  int32: Int32Array,
  float32: Float32Array,
} as const;

export class TimeseriesDataClient {
  private shape: number = 0;
  private numChannels: number = 1;
  private dtype: DType | null = null;
  private chunkSize: number;
  private cache: ChunkCache = {};
  private inProgressFetches: { [key: number]: Promise<SupportedTypedArray> } =
    {};
  private datasetJsonUrl: string;
  private datasetDataUrl: string;

  constructor(
    datasetJsonUrl: string,
    datasetDataUrl: string,
    chunkSize: number = 100000,
  ) {
    this.datasetJsonUrl = datasetJsonUrl;
    this.datasetDataUrl = datasetDataUrl;
    this.chunkSize = chunkSize;
  }

  static async create(
    datasetJsonUrl: string,
    datasetDataUrl: string,
    chunkSize: number = 1000,
  ): Promise<TimeseriesDataClient> {
    const client = new TimeseriesDataClient(
      datasetJsonUrl,
      datasetDataUrl,
      chunkSize,
    );
    await client.initialize();
    return client;
  }

  private async initialize() {
    const infoUrl = this.datasetJsonUrl;
    const response = await fetch(infoUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch dataset info: ${response.statusText}`);
    }
    const info = await response.json();
    
    // Handle multi-dimensional shape: [num_timepoints, num_channels]
    if (Array.isArray(info.shape)) {
      this.shape = info.shape[0];
      this.numChannels = info.shape.length > 1 ? info.shape[1] : 1;
    } else {
      this.shape = info.shape;
      this.numChannels = 1;
    }

    if (!this.isValidDType(info.dtype)) {
      throw new Error(`Unsupported data type: ${info.dtype}`);
    }
    this.dtype = info.dtype;
  }

  private isValidDType(dtype: string): dtype is DType {
    return dtype in TypedArrayConstructors;
  }

  private getChunkIndices(start: number, end: number): number[] {
    const startChunk = Math.floor(start / this.chunkSize);
    const endChunk = Math.floor(end / this.chunkSize);
    const chunks: number[] = [];
    for (let i = startChunk; i <= endChunk; i++) {
      chunks.push(i);
    }
    return chunks;
  }

  private async fetchChunk(chunkIndex: number): Promise<SupportedTypedArray> {
    // Return cached chunk if available
    if (this.cache[chunkIndex]) {
      return this.cache[chunkIndex];
    }

    // If this chunk is already being fetched, wait for it to complete
    const inProgressFetch = this.inProgressFetches[chunkIndex];
    if (inProgressFetch !== undefined) {
      return inProgressFetch;
    }

    // Start new fetch and track it
    const fetchPromise = (async () => {
      if (!this.dtype) {
        throw new Error("Data type not initialized");
      }

      const start = chunkIndex * this.chunkSize;
      const end = Math.min(start + this.chunkSize, this.shape);
      const url = this.datasetDataUrl;
      const itemSize = TypedArrayConstructors[this.dtype].BYTES_PER_ELEMENT;
      // Account for multi-channel data: each timepoint has numChannels values
      const byteStart = start * this.numChannels * itemSize;
      const byteEnd = end * this.numChannels * itemSize;

      try {
        const response = await fetch(url, {
          headers: {
            Range: `bytes=${byteStart}-${byteEnd - 1}`,
          },
        });
        if (!response.ok) {
          throw new Error(`Failed to fetch chunk: ${response.statusText}`);
        }

        const buffer = await response.arrayBuffer();
        const ArrayConstructor = TypedArrayConstructors[this.dtype];
        const data = new ArrayConstructor(buffer);
        this.cache[chunkIndex] = data;
        return data;
      } finally {
        // Clean up the in-progress fetch regardless of success/failure
        delete this.inProgressFetches[chunkIndex];
      }
    })();

    // Store the promise for other requests to wait on
    this.inProgressFetches[chunkIndex] = fetchPromise;
    return fetchPromise;
  }

  async fetchRange(start: number, end: number, channel: number = 0): Promise<SupportedTypedArray> {
    if (!this.dtype) {
      throw new Error("Data type not initialized");
    }

    if (channel < 0 || channel >= this.numChannels) {
      throw new Error(`Invalid channel ${channel}. Must be between 0 and ${this.numChannels - 1}`);
    }

    const chunkIndices = this.getChunkIndices(start, end);
    const chunks = await Promise.all(
      chunkIndices.map((idx) => this.fetchChunk(idx)),
    );

    // Calculate total length needed
    const length = end - start;
    const ArrayConstructor = TypedArrayConstructors[this.dtype];
    const result = new ArrayConstructor(length);

    // Copy data from chunks into result array
    let resultOffset = 0;
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const chunkStart = chunkIndices[i] * this.chunkSize;
      const copyStart = Math.max(0, start - chunkStart);
      const copyEnd = Math.min(chunk.length / this.numChannels, end - chunkStart);
      
      // Extract the selected channel from interleaved data
      for (let t = copyStart; t < copyEnd; t++) {
        const sourceIdx = t * this.numChannels + channel;
        result[resultOffset++] = chunk[sourceIdx];
      }
    }

    return result;
  }

  getShape(): number {
    return this.shape;
  }

  getDType(): DType | null {
    return this.dtype;
  }

  getNumChannels(): number {
    return this.numChannels;
  }
}

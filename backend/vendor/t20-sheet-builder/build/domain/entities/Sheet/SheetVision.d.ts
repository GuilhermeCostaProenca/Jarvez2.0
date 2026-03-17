import { type SheetVisionInterface } from './SheetVisionInterface';
import { Vision } from './Vision';
export declare class SheetVision implements SheetVisionInterface {
    private vision;
    constructor(vision?: Vision);
    changeVision(vision: Vision): void;
    getVision(): Vision;
}

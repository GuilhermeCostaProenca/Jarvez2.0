import { SizeName } from './SizeName';
export type Size = {
    name: SizeName;
    occupiedSpaceInMeters: number;
    maneuversModifier: number;
    furtivityModifier: number;
};
export declare const sizes: Record<SizeName, Size>;

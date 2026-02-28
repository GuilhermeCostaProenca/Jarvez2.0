import { type Size } from '../Size/Size';
import { SizeName } from '../Size/SizeName';
import { type SheetSizeInterface } from './SheetSizeInterface';
export declare class SheetSize implements SheetSizeInterface {
    private size;
    constructor(size?: Size);
    changeSize(size: Size): void;
    getSize(): SizeName;
    getOccupiedSpaceInMeters(): number;
    getManeuversModifier(): number;
    getFurtivityModifier(): number;
}

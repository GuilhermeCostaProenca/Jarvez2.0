import { type SheetDisplacementInterface } from './SheetDisplacementInterface';
export declare class SheetDisplacement implements SheetDisplacementInterface {
    private displacement;
    private climbingDisplacement;
    constructor(displacement?: number);
    changeDisplacement(displacement: number): void;
    changeClimbingDisplacement(climbingDisplacement: number): void;
    getDisplacement(): number;
    getClimbingDisplacement(): number | undefined;
}

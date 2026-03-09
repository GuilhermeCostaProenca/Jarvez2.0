import { Equipment } from '../Equipment';
import type { EquipmentName } from '../EquipmentName';
export declare class EquipmentAdventure extends Equipment {
    readonly name: EquipmentName;
    readonly isWieldable: boolean;
    readonly price: number;
    categoryForImprovement: null;
    constructor(name: EquipmentName, isWieldable?: boolean, price?: number);
}

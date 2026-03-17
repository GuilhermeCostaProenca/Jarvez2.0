import { Equipment } from '../Equipment';
import type { EquipmentName } from '../EquipmentName';
export declare class EquipmentAnimal extends Equipment {
    readonly name: EquipmentName;
    readonly price: number;
    categoryForImprovement: null;
    get isWieldable(): boolean;
    constructor(name: EquipmentName, price?: number);
}

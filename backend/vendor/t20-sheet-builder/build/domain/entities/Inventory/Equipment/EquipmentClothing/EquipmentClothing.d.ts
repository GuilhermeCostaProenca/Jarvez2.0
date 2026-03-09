import { Equipment } from '../Equipment';
import { EquipmentImprovementCategory } from '../EquipmentImprovement/EquipmentImprovementCategory';
import type { EquipmentName } from '../EquipmentName';
export declare class EquipmentClothing extends Equipment {
    readonly name: EquipmentName;
    readonly price: number;
    categoryForImprovement: EquipmentImprovementCategory;
    get isWieldable(): boolean;
    constructor(name: EquipmentName, price?: number);
}

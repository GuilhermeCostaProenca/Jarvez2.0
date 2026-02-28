import { Equipment } from '../Equipment';
import type { EquipmentName } from '../EquipmentName';
export type EquipmentWizardFocusName = EquipmentName.wand | EquipmentName.staff;
export declare class EquipmentWizardFocus extends Equipment {
    readonly name: EquipmentWizardFocusName;
    readonly isWieldable: boolean;
    readonly price: number;
    categoryForImprovement: null;
    constructor(name: EquipmentWizardFocusName, isWieldable?: boolean, price?: number);
}

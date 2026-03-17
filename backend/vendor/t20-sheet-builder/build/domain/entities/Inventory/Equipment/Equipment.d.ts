import { type CharacterModifiers } from '../../Character/CharacterModifiers';
import { type SerializedSheetEquipment } from '../../Sheet';
import { type EquipmentImprovement } from './EquipmentImprovement/EquipmentImprovement';
import { EquipmentImprovementCategory } from './EquipmentImprovement/EquipmentImprovementCategory';
import type { EquipmentName } from './EquipmentName';
export declare abstract class Equipment<T extends EquipmentName = EquipmentName> {
    static improvementPrices: number[];
    readonly improvements: EquipmentImprovement[];
    abstract readonly name: T;
    abstract readonly isWieldable: boolean;
    abstract price: number;
    abstract readonly categoryForImprovement: EquipmentImprovementCategory | null;
    addImprovement(improvement: EquipmentImprovement): void;
    getTotalPrice(): number;
    serialize(): SerializedSheetEquipment<T>;
    onEquip(modifiers: CharacterModifiers): void;
    onUnequip(modifiers: CharacterModifiers): void;
}

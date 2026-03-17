import { type CharacterModifiers } from '../Character/CharacterModifiers';
import { type SerializedSheetInventoryEquipment } from '../Sheet';
import type { Equipment } from './Equipment';
export declare class InventoryEquipment<T extends Equipment = Equipment> {
    readonly equipment: T;
    private isEquipped;
    private quantity;
    constructor(equipment: T, isEquipped?: boolean);
    toggleEquipped(modifiers: CharacterModifiers): void;
    getQuantity(): number;
    increaseQuantity(): void;
    getIsEquipped(): boolean;
    serialize(): SerializedSheetInventoryEquipment;
}

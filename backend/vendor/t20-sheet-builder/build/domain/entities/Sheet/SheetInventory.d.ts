import { type Armor, EquipmentName, type Equipment } from '../Inventory';
import { Inventory } from '../Inventory/Inventory';
import { type InventoryEquipment } from '../Inventory/InventoryEquipment';
import { type SerializedSheetInventoryEquipment } from './SerializedSheet';
import { type SerializedInitialEquipment, type AddInitialEquipmentParams, type SheetInventoryInterface, type ToggleEquippedItemParams } from './SheetInventoryInterface';
import { type TransactionInterface } from './TransactionInterface';
export declare class SheetInventory implements SheetInventoryInterface {
    private readonly inventory;
    static readonly initialArmors: Set<EquipmentName>;
    static readonly initialArmorsForHeavyProficients: Set<EquipmentName>;
    private initialEquipment?;
    constructor(inventory?: Inventory);
    serializeInitialEquipment(): SerializedInitialEquipment | undefined;
    serialize(): SerializedSheetInventoryEquipment[];
    getArmorBonus(): number;
    getShieldBonus(): number;
    toggleEquippedItem({ maxWieldedItems, modifiers, name }: ToggleEquippedItemParams): void;
    addEquipment(equipment: Equipment, isEquipped?: boolean): void;
    addInitialEquipment(params: AddInitialEquipmentParams, transaction: TransactionInterface): void;
    getArmor(): InventoryEquipment<Armor<import("../Inventory").ArmorName>> | undefined;
    getShield(): InventoryEquipment<import("../Inventory/Equipment/Weapon/DefensiveWeapon/Shield/Shield").Shield> | undefined;
    addMoney(quantity: number): void;
    removeMoney(quantity: number): void;
    getMoney(): number;
    getEquipment(name: EquipmentName): InventoryEquipment | undefined;
    getWieldedItems(): EquipmentName[];
    getEquipments(): Map<EquipmentName, InventoryEquipment<Equipment<EquipmentName>>>;
    private validateInitialWeapons;
}

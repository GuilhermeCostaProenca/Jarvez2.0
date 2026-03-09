import { Armor, type EquipmentName } from './Equipment';
import type { Equipment } from './Equipment/Equipment';
import { Shield } from './Equipment/Weapon/DefensiveWeapon/Shield/Shield';
import { InventoryEquipment } from './InventoryEquipment';
export declare class Inventory {
    equipments: Map<EquipmentName, InventoryEquipment<Equipment<EquipmentName>>>;
    money: number;
    addEquipment(equipment: Equipment, isEquipped?: boolean): void;
    addMoney(amount: number): void;
    removeMoney(amount: number): void;
    getItem(name: EquipmentName): InventoryEquipment<Equipment<EquipmentName>> | undefined;
    getEquipments(): Map<EquipmentName, InventoryEquipment<Equipment<EquipmentName>>>;
    getArmor(): InventoryEquipment<Armor> | undefined;
    getShield(): InventoryEquipment<Shield> | undefined;
    getWieldedItems(): EquipmentName[];
    getMoney(): number;
}

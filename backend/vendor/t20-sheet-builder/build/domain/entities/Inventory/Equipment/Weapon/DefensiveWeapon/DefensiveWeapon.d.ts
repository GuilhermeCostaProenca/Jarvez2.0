import { type CharacterModifiers } from '../../../../Character/CharacterModifiers';
import { type EquipmentName } from '../../EquipmentName';
import type { WeaponType } from '../Weapon';
import { Weapon } from '../Weapon';
export declare abstract class DefensiveWeapon<T extends EquipmentName = EquipmentName> extends Weapon<T> {
    abstract defenseBonus: number;
    abstract armorPenalty: number;
    abstract slots: number;
    get type(): WeaponType;
    private modifierIndex;
    onEquip(modifiers: CharacterModifiers): void;
    onUnequip(modifiers: CharacterModifiers): void;
}

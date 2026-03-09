import type { Proficiency } from '../../../Sheet/Proficiency';
import { Equipment } from '../Equipment';
import { type EquipmentName } from '../EquipmentName';
export type WeaponType = 'offensive' | 'defensive' | 'exotic' | 'firearm';
export declare abstract class Weapon<T extends EquipmentName = EquipmentName> extends Equipment<T> {
    readonly proficiency: Proficiency;
    abstract readonly type: WeaponType;
    constructor(proficiency: Proficiency);
}

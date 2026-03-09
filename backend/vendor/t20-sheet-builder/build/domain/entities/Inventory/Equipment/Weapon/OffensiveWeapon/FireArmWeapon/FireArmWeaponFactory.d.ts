import { type SerializedSheetEquipment } from '../../../../../Sheet';
import { type FireArmWeapon } from './FireArmWeapon';
import { type FireArmWeaponName } from './FireArmWeaponName';
export declare class FireArmWeaponFactory {
    static makeFromSerialized(serialized: SerializedSheetEquipment<FireArmWeaponName>): FireArmWeapon;
}

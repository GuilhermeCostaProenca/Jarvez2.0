import { type SerializedSheetEquipment } from '../../../../../Sheet';
import { type ExoticWeapon } from './ExoticWeapon';
import { type ExoticWeaponName } from './ExoticWeaponName';
export declare class ExoticWeaponFactory {
    static makeFromSerialized(serialized: SerializedSheetEquipment<ExoticWeaponName>): ExoticWeapon;
}

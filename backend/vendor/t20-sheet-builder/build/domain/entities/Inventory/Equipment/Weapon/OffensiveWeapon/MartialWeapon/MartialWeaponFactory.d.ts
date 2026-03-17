import { type SerializedSheetEquipment } from '../../../../../Sheet';
import { type MartialWeapon } from './MartialWeapon';
import { type MartialWeaponName } from './MartialWeaponName';
export declare class MartialWeaponFactory {
    static makeFromSerialized(serialized: SerializedSheetEquipment<MartialWeaponName>): MartialWeapon;
}

import { type SerializedSheetEquipment } from '../../../../../Sheet';
import { type SimpleWeapon } from './SimpleWeapon';
import { type SimpleWeaponName } from './SimpleWeaponName';
export declare class SimpleWeaponFactory {
    static makeFromSerialized(serialized: SerializedSheetEquipment<SimpleWeaponName>): SimpleWeapon;
}

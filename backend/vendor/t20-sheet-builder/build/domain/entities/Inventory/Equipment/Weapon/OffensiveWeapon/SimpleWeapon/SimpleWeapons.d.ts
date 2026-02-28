import { type SimpleWeaponStatic } from './SimpleWeaponStatic';
import { type SimpleWeaponName } from './SimpleWeaponName';
export declare class SimpleWeapons {
    static map: Record<SimpleWeaponName, SimpleWeaponStatic>;
    static getAll(): SimpleWeaponStatic[];
    static getByName(name: SimpleWeaponName): SimpleWeaponStatic;
}

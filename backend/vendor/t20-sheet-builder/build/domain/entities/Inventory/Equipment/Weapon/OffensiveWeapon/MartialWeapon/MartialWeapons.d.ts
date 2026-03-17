import { type MartialWeaponName } from './MartialWeaponName';
import { type MartialWeaponStatic } from './MartialWeaponStatic';
export declare class MartialWeapons {
    static map: Record<MartialWeaponName, MartialWeaponStatic>;
    static getAll(): MartialWeaponStatic[];
    static getByName(name: MartialWeaponName): MartialWeaponStatic;
}

import { OffensiveWeapon } from '../OffensiveWeapon';
import { type MartialWeaponName } from './MartialWeaponName';
export declare abstract class MartialWeapon extends OffensiveWeapon<MartialWeaponName> {
    abstract name: MartialWeaponName;
    constructor();
}

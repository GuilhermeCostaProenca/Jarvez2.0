import { OffensiveWeapon } from '../OffensiveWeapon';
import { type SimpleWeaponName } from './SimpleWeaponName';
export declare abstract class SimpleWeapon extends OffensiveWeapon<SimpleWeaponName> {
    abstract name: SimpleWeaponName;
    constructor();
}

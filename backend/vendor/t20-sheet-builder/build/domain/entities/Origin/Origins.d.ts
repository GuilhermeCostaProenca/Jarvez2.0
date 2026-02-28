import { OriginName } from './OriginName';
import { type OriginStatic } from './OriginStatic';
export declare class Origins {
    static getAll(): OriginStatic[];
    static getByName(name: OriginName): OriginStatic | undefined;
    private static readonly map;
}

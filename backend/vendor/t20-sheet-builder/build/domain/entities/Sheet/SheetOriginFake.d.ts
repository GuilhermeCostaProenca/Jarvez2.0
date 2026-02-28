import { type OriginInterface } from '../Origin/Origin';
import { type SheetOriginInterface } from './SheetOriginInterface';
export declare class SheetOriginFake implements SheetOriginInterface {
    origin: OriginInterface | undefined;
    chooseOrigin: import("vitest").Mock<any, any>;
    constructor(origin?: OriginInterface | undefined);
    getOrigin(): OriginInterface | undefined;
}
